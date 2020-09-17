import logging
logger = logging.getLogger('bungie')


class History:
    def __init__(self):
        self.by_param = {}
        self.by_msg = {}
        self.all_bindings = {}

    def check_integrity(self, message):
        """
        Make sure payload can be received.

        Each message in enactment should have the same keys.
        Returns true if the parameters are consistent with all messages in the matching enactment.
        """
        # may not the most efficient algorithm for large histories
        # might be better to ask the database to find messages that don't match
        enactment = self.enactment(message)
        result = all(message.payload[p] == m[p]
                     for p in message.payload.keys()
                     for m in enactment
                     if p in m)
        if result:
            return enactment

    def check_outs(self, message):
        """
        Make sure none of the outs have been previous bound to a different value.
        Only use this check if the message is being sent.
        """
        # get the list of messages that have matching keys
        enactment = [m for l in self.by_param.get(next(k for k in message.schema.keys), {}).values()
                     for m in l
                     if all(m.payload.get(p) == message.payload.get(p) for p in message.schema.keys)]
        # make sure none of them have a different binding for any out parameters
        # any messages with existing bindings must be duplicates
        return not any(m.payload.get(p) and not m.schema == message.schema
                       for m in enactment
                       for p in message.schema.outs)

    def check_dependencies(self, message):
        """
        Make sure that all 'in' parameters are bound and matched by some message in the history
        """
        return not any(message.payload[p] not in self.all_bindings.get(p, {})
                       for p in message.schema.ins)

    def validate_send(self, message):
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
                    self.by_param[k][v].add(message)
                else:
                    self.by_param[k][v] = {message}
            else:
                self.by_param[k] = {v: {message}}

    def enactment(self, message):
        enactment = {'messages': set()}
        matches = {}
        for k in message.schema.keys:
            if k in message.payload:
                matches[k] = self.by_param.get(
                    k, {}).get(message.payload[k], set()).copy()
                matches[k].add(message)
                enactment['messages'].update(matches[k])
                # may need to filter parameters
            else:
                matches[k] = set(message)
        enactment['history'] = matches

        preds = None
        for k in message.schema.keys:
            preds = preds or matches[k]
            preds = filter(lambda m: k not in m.payload or m.payload.get(
                k) == message.payload.get(k), preds)

        enactment["bindings"] = {
            k: v for m in preds for k, v in m.payload.items()}
        return enactment

    def duplicate(self, message):
        """
        Return true if payload has been observed before.
        Somewhat expensive linear scan of all messages with the same schema.
        """
        match = self.by_msg.get(message.schema, {}).get(message.key)
        if match and all(message.payload.get(p) == match.payload.get(p)
                         for p in message.payload):
            return True
        elif match:
            raise Exception(
                "Message found with matching key {} but different parameters: {}, {}".format(
                    message.key, message, match))
        else:
            return False

    def acknowledge(self, message):
        match = self.by_msg[message.schema].get(message.key)
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
