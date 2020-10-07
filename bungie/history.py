import logging
logger = logging.getLogger('bungie')


class Enactment:
    def __init__(self, parent=None):
        self.subenactments = {}
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
        return f"Enactment(bindings={self.bindings},messages={[m for m in self.messages]},subenactments={self.subenactments})"


class History:
    def __init__(self):
        # message index
        self.messages = {}

        # parameter indexes
        self.all_bindings = {}
        self.bindings = {}

        # recursive (key -> value -> enactment -> subkey -> value -> subenactment...)
        self.enactments = {}

    def check_integrity(self, message):
        """
        Make sure payload can be received.

        Each message in enactment should have the same keys.
        Returns true if the parameters are consistent with all messages in the matching enactment.
        """
        bindings = self.bindings.get(message.key, {})
        result = all(message.payload[p] == bindings[p]
                     for p in message.payload
                     if p in bindings)
        return result

    def check_outs(self, message):
        """
        Make sure none of the outs have been previous bound to a different value.
        Only use this check if the message is being sent.
        Assumes message is not a duplicate.
        """
        return not any(p in self.bindings.get(message.key, {}) for p in message.schema.outs)

    def check_dependencies(self, message):
        """
        Make sure that all 'in' parameters are bound and matched by some message in the history
        """
        return not any(message.payload[p] not in self.all_bindings.get(p, [])
                       for p in message.schema.ins)

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

        # record all unique parameter bindings
        for p in message.payload:
            if p in self.all_bindings:
                self.all_bindings[p].add(message.payload[p])
            else:
                self.all_bindings[p] = set([message.payload[p]])

        # log under the correct enactment
        enactment = self.enactment(message)
        enactment.add(message)

    def enactment(self, message):
        enactments = self.enactments
        enactment = None
        for k in message.schema.keys:
            # assume sequential hierarchy of key parameters
            v = message.payload.get(k)
            if k in enactments:
                if v is not None and v in enactments[k]:
                    enactment = enactments[k][v]
                    enactments = enactment.subenactments
                else:
                    enactment = enactments[k][v] = Enactment(parent=enactment)
            else:
                enactments[k] = {}
                enactment = enactments[k][v] = Enactment(parent=enactment)
        return enactment

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
                    message.key, message, match))
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
        Enactment = self.enactment(message)
        bindings = enactment.bindings

        for p in message.schema.parameters:
            v = bindings.get(p)
            if v:
                message.payload[p] = v
            else:
                raise Exception(
                    f"Cannot complete message {message} with enactment {enactment}")
        return message
