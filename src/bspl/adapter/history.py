import logging
logger = logging.getLogger('bungie')


class History:
    def __init__(self):
        # message indexes
        self.by_param = {}
        self.by_msg = {}

        # parameter indexes
        self.all_bindings = {}
        self.bindings = {}

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

        if self.duplicate(message):
            self.by_msg[message.schema][message.key].duplicate = True
            return

        # log by message type
        if message.schema in self.by_msg:
            self.by_msg[message.schema][message.key] = message
        else:
            self.by_msg[message.schema] = {message.key: message}

        # record all unique parameter bindings
        for p in message.payload:
            if p in self.all_bindings:
                self.all_bindings[p].add(message.payload[p])
            else:
                self.all_bindings[p] = set([message.payload[p]])

        # log message under each key
        for k in message.schema.keys:
            v = message.payload.get(k)
            if v is not None and k in self.by_param:
                if v in self.by_param[k]:
                    d = self.by_param[k][v]
                    d['all'].add(message)
                    if message.schema in d:
                        d[message.schema].add(message)
                    else:
                        d[message.schema] = {message}
                else:
                    self.by_param[k][v] = {
                        'all': {message},
                        message.schema: {message}
                    }
            else:
                self.by_param[k] = {
                    v: {'all': {message}, message.schema: {message}}}

        # update bindings
        if message.key in self.bindings:
            bs = self.bindings[message.key]
            for p in message.payload:
                if p not in bs:
                    bs[p] = message.payload[p]
        else:
            self.bindings[message.key] = message.payload.copy()

    def enactment(self, message):
        enactment = {"bindings": self.bindings.get(message.key)}
        return enactment

    def duplicate(self, message):
        """
        Return true if payload has been observed before.
        """
        match = self.by_msg.get(message.schema, {}).get(message.key)
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
        match = self.by_msg[schema].get(key)
        if match:
            if match.acknowledged:
                return True
            else:
                match.acknowledged = True

    def fill(self, message):
        enactment = self.enactment(message)
        for p in message.schema.parameters:
            v = enactment['bindings'].get(p)
            if v:
                message.payload[p] = v
            else:
                raise Exception(
                    "Cannot complete message {} with enactment {}".format(message, enactment))
        return message
