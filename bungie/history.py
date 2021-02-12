import logging

logger = logging.getLogger("bungie")


def get_key(schema, payload):
    # schema.keys should be ordered, or sorted for consistency
    return ",".join(k + ":" + str(payload[k]) for k in schema.keys)


class Message:
    schema = None
    payload = {}
    acknowledged = False
    dest = None
    adapter = None
    meta = {}
    key = None

    def __init__(self, schema, payload, acknowledged=False, dest=None, adapter=None):
        self.schema = schema
        self.payload = payload
        self.acknowledged = acknowledged
        self.dest = dest
        self.adapter = adapter
        self.meta = {}
        print(f"schema: {self.schema}")
        self.key = get_key(self.schema, self.payload)

    def __repr__(self):
        payload = ",".join("{0}={1!r}".format(k, v) for k, v in self.payload.items())
        return f"{self.schema.name}({payload})"

    def __eq__(self, other):
        return self.payload == other.payload and self.schema == other.schema

    def __hash__(self):
        return hash(self.schema.qualified_name + self.key)

    def __getitem__(self, name):
        return self.payload[name]

    def __setitem__(self, name, value):
        self.payload[name] = value
        return value

    def __getattr__(self, key):
        return self.payload[name]

    def __setattr__(self, name, value):
        if hasattr(self, name):
            super().__setattr__(name, value)
        else:
            self.payload[name] = value
        return value

    def keys_match(self, other):
        return all(
            self.payload[k] == other.payload[k]
            for k in self.schema.keys
            if k in other.schema.parameters
        )

    def ack(self):
        payload = {k: self.payload[k] for k in self.schema.keys}
        payload["$ack"] = self.schema.name
        self.acknowledged = True
        schema = self.schema.acknowledgment()
        return Message(schema, payload)

    def project_key(self, schema):
        key = []
        # use ordering from other schema
        for k in schema.keys:
            if k in self.schema.keys:
                key.append(k)
        return ",".join(k + ":" + str(self.payload[k]) for k in key)


class Context:
    def __init__(self, parent=None):
        self.subecontexts = {}
        self._bindings = {}
        self._messages = []
        self.parent = parent

    def add(self, message):
        self._bindings.update(message.payload)
        self._messages.append(message)

    @property
    def bindings(self):
        # may not be efficient enough, since it collects all of the
        # bindings every time it's accessed
        if self.parent:
            return {**self.parent.bindings, **self._bindings}
        else:
            return self._bindings

    @property
    def messages(self):
        if self.parent:
            yield from self.parent.messages
        yield from self._messages

    def __repr__(self):
        return f"Context(bindings={self.bindings},messages={[m for m in self.messages]},subcontexts={self.subcontexts})"

    def instance(self, schema):
        payload = {}
        for k in schema.parameters:
            payload[k] = self.bindings[k]
        return Message(schema, payload)


class History:
    def __init__(self):
        # message indexes
        self.messages = {}
        self.by_param = {}

        # parameter indexes
        self.bindings = {}

        # recursive (key -> value -> context -> subkey -> value -> subcontext...)
        self.contexts = {}

    def match(self, **params):
        """Find messages that either have the same bindings, or don't have the parameter"""
        candidates = set()
        for p, v in params:
            # collect all candidates that match on any parameter
            candidates.update(self.by_param[p][v])

    def check_integrity(self, message):
        """
        Make sure payload can be received.

        Each message in context should have the same keys.
        Returns true if the parameters are consistent with all messages in the matching context.
        """
        bindings = self.bindings.get(message.key, {})
        result = all(
            message.payload[p] == bindings[p] for p in message.payload if p in bindings
        )
        return result

    def check_outs(self, message):
        """
        Make sure none of the outs have been previous bound to a different value.
        Only use this check if the message is being sent.
        Assumes message is not a duplicate.
        """
        return not any(
            p in self.bindings.get(message.key, {}) for p in message.schema.outs
        )

    def check_dependencies(self, message):
        """
        Make sure that all 'in' parameters are bound and matched by some message in the history
        """
        return not any(
            message.payload[p] not in self.all_bindings.get(p, [])
            for p in message.schema.ins
        )

    def validate_send(self, message):
        # message assumed not to be duplicate; otherwise recheck unnecessary

        if not self.check_outs(message):
            logger.info("Failed out check: {}".format(message.payload))
            return False

        if not self.check_integrity(message):
            logger.info("Failed integrity check: {}".format(message.payload))
            return False

        if not self.check_dependencies(message):
            logger.info("Failed dependency check: {}".format(message.payload))
            return False

        return True

    def observe(self, message):
        """Observe an instance of a given message specification.
        Check integrity, and add the message to the history."""

        # index messages by key
        if message.schema in self.messages:
            self.messages[message.schema][message.key] = message
        else:
            self.messages[message.schema] = {message.key: message}

        # update bindings
        if message.key in self.bindings:
            bs = self.bindings[message.key]
            for p in message.payload:
                if p not in bs:
                    bs[p] = message.payload[p]
        else:
            self.bindings[message.key] = message.payload.copy()

        # log under the correct context
        context = self.context(message)
        context.add(message)

    def context(self, message):
        contexts = self.contexts
        context = None
        for k in message.schema.keys:
            # assume sequential hierarchy of key parameters
            v = message.payload.get(k)
            if k in contexts:
                if v is not None and v in contexts[k]:
                    context = contexts[k][v]
                    contexts = context.subcontexts
                else:
                    context = contexts[k][v] = Context(parent=context)
            else:
                contexts[k] = {}
                context = contexts[k][v] = Context(parent=context)
        return context

    def duplicate(self, message):
        """
        Return true if payload has been observed before.
        """
        match = self.messages.get(message.schema, {}).get(message.key)
        if match and match == message:
            return True
        elif match:
            raise Exception(
                "Message found with matching key {} but different parameters: {}, {}".format(
                    message.key, message, match
                )
            )
        else:
            return False

    def acknowledge(self, schema, key):
        """
        Mark a matching message as acknowledged
        Return True if it had already been acknowledged
        """
        match = self.messages[schema].get(key)
        if match:
            if match.acknowledged:
                return True
            else:
                match.acknowledged = True

    def fill(self, message):
        context = self.context(message)
        bindings = context.bindings

        for p in message.schema.parameters:
            v = bindings.get(p)
            if v:
                message.payload[p] = v
            else:
                raise Exception(
                    f"Cannot complete message {message} with context {context}"
                )
        return message
