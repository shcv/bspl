import logging
import json
import datetime
from threading import Thread
import sys
import os
import math
import socket
from queue import Queue

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger('bungie')


class History:
    def __init__(self):
        self.log = {}
        self.parameters = {}


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
        Make sure none of the outs have been bound.
        Only use this check if the message is being sent.
        """
        enactment = [m for l in self.log.get(next(k for k in message.schema.keys), {}).values()
                     for m in l
                     if all(m.payload.get(p) == message.payload.get(p) for p in message.schema.keys)]
        return not any(m.payload.get(p)
                       for m in enactment
                       for p in message.schema.outs)

    def check_dependencies(self, message):
        """
        Make sure that all 'in' parameters are bound and matched by some message in the history
        """
        return not any(message.payload[p] not in self.parameters.get(p, {})
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
        for p in message.payload:
            if p in self.parameters:
                self.parameters[p].add(message.payload[p])
            else:
                self.parameters[p] = set([message.payload[p]])

        for k in message.schema.keys:
            v = message.payload.get(k)
            if v and self.log.get(k):
                if self.log[k].get(v):
                    self.log[k][v].append(message)
                else:
                    self.log[k][v] = [message]
            else:
                self.log[k] = {v: [message]}


    def enactment(self, message):
        enactment = {'messages': set()}
        matches = {}
        for k in message.schema.keys:
            if message.payload.get(k):
                matches[k] = self.log.get(k, {}).get(message.payload[k], [])
                enactment['messages'].update(matches[k])
                # may need to filter parameters
            else:
                matches[k] = []
        enactment['history'] = matches

        preds = None
        for k in message.schema.keys:
            preds = preds or matches[k]
            preds = filter(lambda m: m.payload.get(
                k) == message.payload.get(k), preds)

        enactment["bindings"] = {
            k: v for m in preds for k, v in m.payload.items()}
        return enactment

    def duplicate(self, message):
        """Return true if payload has been observed before"""
        for k, v in message.payload.items():
            if v in self.log.get(k, {}):
                log = self.log[k][v]
                if len(log) and all(message.payload.get(p) == m.payload.get(p)
                                    for p in message.payload
                                    for m in log):
                    return True


class Message:
    def __init__(self, schema, payload, enactment=None, duplicate=False):
        self.schema = schema
        self.payload = payload
        self.enactment = enactment
        self.duplicate = duplicate

    def __str__(self):
        if self.enactment and self.duplicate:
            return "Message({}, {}, {}, {})".format(
                self.schema.name, self.payload, self.enactment, self.duplicate)
        elif self.enactment:
            return "Message({}, {}, {})".format(
                self.schema.name, self.payload, self.enactment)
        elif self.duplicate:
            return "Message({}, {}, duplicate={})".format(
                self.schema.name, self.payload, self.duplicate)
        else:
            return "Message({}, {})".format(self.schema.name, self.payload)


class Adapter:
    def __init__(self, role, protocol, configuration):
        """
        Initialize the PoS adapter.

        role: name of the role being implemented
        protocol: a protocol specification
          {name, keys, messages: [{name, from, to, parameters, keys, ins, outs, nils}]}
        configuration: a dictionary of roles to endpoint URLs
          {role: url}
        """
        self.role = role
        self.protocol = protocol
        self.configuration = configuration
        self.sent_handlers = {}
        self.received_handlers = {}
        self.history = History()
        self.send_q = Queue()
        self.recv_q = Queue()
        self.process_thread = Thread(target=self.process_loop)
        self.listen_thread = Thread(target=self.listen_loop)

    def process_receive(self, payload):
        if not isinstance(payload, dict):
            logger.warn(
                "Payload does not parse to a dictionary: {}".format(payload))
            return

        schema = self.protocol.find_schema(payload, to=self.role)
        if not schema:
            logger.warn("No schema matching payload: {}".format(payload))
            return
        message = Message(schema, payload)
        message.enactment = self.history.check_integrity(message)
        if message.enactment is not False:
            if self.history.duplicate(message):
                logger.debug("Duplicate message: {}".format(message))
                message.duplicate = True
            else:
                logger.debug("Observing message: {}".format(message))
                self.history.observe(message)

            reactor = self.received_handlers.get(schema)
            if reactor:
                logger.debug("Invoking reactor: {}".format(reactor))
                # run reactor in a thread
                Thread(target=reactor, args=(message,)).start()

    def send(self, payload, schema=None, name=None, to=None):
        """
        Add a message to the outgoing queue
        """
        schema = schema or self.protocol.find_schema(payload, name=name, to=to)
        self.send_q.put(Message(schema, payload))

    def process_send(self, message):
        """
        Send a message by posting to the recipient's http endpoint,
        after checking for correctness, and storing the message.
        """
        enactment = self.history.enactment(message)
        dest = self.configuration[message.schema.recipient]

        if self.history.validate_send(message):
            self.history.observe(message)

            reactor = self.sent_handlers.get(message.schema)
            if reactor:
                logger.info("Invoking reactor: {}".format(reactor))
                # run reactor in a thread
                threading.Thread(target=reactor, args=(message,)).start()

            logger.debug("Sending message {} to {} at {}".format(
                message.payload, message.schema.recipient.name, dest))

            data = json.dumps(message.payload).encode('utf-8')
            if len(data) > 1500-48:  # ethernet MTU - IPv6 + UDP header
                logger.info("Message too long: {}".format(data))

            sock = socket.socket(socket.AF_INET,  # Internet
                                 socket.SOCK_DGRAM)  # UDP
            sock.sendto(data, dest)
            return True

    def sent(self, schema):
        """
        Decorator for declaring sent message handlers.

        Example:
        @adapter.sent(MessageSchema)
        def handle_message(message, enactment):
            'do stuff'
        """
        def register_handler(handler):
            self.sent_handlers[schema] = handler
        return register_handler

    def received(self, schema):
        """
        Decorator for declaring received message handlers.

        Example:
        @adapter.received(MessageSchema)
        def handle_message(message, enactment):
            'do stuff'
        """
        def register_handler(handler):
            self.received_handlers[schema] = handler
        return register_handler

    def listen_loop(self):
        sock = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_DGRAM)  # UDP
        sock.bind(self.configuration[self.role])  # (IP, port)

        while True:
            data, addr = sock.recvfrom(1500)  # buffer size is 1500 bytes
            self.recv_q.put(json.loads(data))

    def process_loop(self):
        while True:
            # very busy waiting...
            if not self.send_q.empty():
                self.process_send(self.send_q.get())
            if not self.recv_q.empty():
                self.process_receive(self.recv_q.get())

    def start(self):
        self.process_thread.start()
        self.listen_thread.start()
