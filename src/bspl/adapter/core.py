import logging
import json
import datetime
from threading import Thread
import sys
import os
import math
import socket
import inspect
import yaml
from queue import Queue
from .history import History
from functools import partial
from .emitter import Emitter, udp_transmitter
from .receiver import Receiver, udp_listener
from .scheduler import Scheduler
from . import policies

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger('bungie')


class Message:
    def __init__(self, schema, payload, enactment=None, duplicate=False, acknowledged=False, dest=None):
        self.schema = schema
        self.payload = payload
        self.enactment = enactment
        self.duplicate = duplicate
        self.acknowledged = acknowledged
        self.dest = dest
        self.meta = {}

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

    def keys_match(self, other):
        return all(self.payload[k] == other.payload[k]
                   for k in self.schema.keys
                   if k in other.schema.parameters)

    @property
    def key(self):
        return tuple(self.payload[k] for k in sorted(self.schema.keys))

    @key.setter
    def set_key(self, value):
        for k, i in enumerate(sorted(self.schema.keys.keys())):
            self.payload[k] = value[i]


class Adapter:
    def __init__(self,
                 role,
                 protocol,
                 configuration,
                 emitter=Emitter(udp_transmitter),
                 receiver=None):
        """
        Initialize the agent adapter.

        role: name of the role being implemented
        protocol: a protocol specification
          {name, keys, messages: [{name, from, to, parameters, keys, ins, outs, nils}]}
        configuration: a dictionary of roles to endpoint URLs
          {role: url}
        """
        self.role = role
        self.protocol = protocol
        self.configuration = configuration
        self.reactors = {}  # dict of message -> {handlers}
        self.history = History()
        self.send_q = Queue()
        self.recv_q = Queue()
        self.process_thread = Thread(target=self.process_loop)
        self.emitter = emitter
        self.receiver = receiver or Receiver(
            udp_listener(*self.configuration[self.role]))
        self.schedulers = []

    def process_receive(self, payload):
        if not isinstance(payload, dict):
            logger.warn(
                "Payload does not parse to a dictionary: {}".format(payload))
            return

        schema = self.protocol.find_schema(payload, to=self.role)
        if not schema:
            logger.warn("No schema matching payload: {}".format(payload))
            return
        elif 'ack' in payload:
            # look up message schema by name
            s = self.protocol.messages[payload['ack']]
            m = Message(s, payload)
            history.acknowledge(m)
        message = Message(schema, payload)
        message.enactment = self.history.check_integrity(message)
        if message.enactment is not False:
            if self.history.duplicate(message):
                logger.debug("Duplicate message: {}".format(message))
                message.duplicate = True
            else:
                logger.debug("Observing message: {}".format(message))
                self.history.observe(message)

            self.react(message)

    def send(self, payload, schema=None, name=None, to=None):
        """
        Add a message to the outgoing queue
        """
        schema = schema or self.protocol.find_schema(payload, name=name, to=to)
        m = Message(schema, payload)
        self.send_q.put(m)

    def resend(self, schema, enactment):
        try:
            m = Message(schema, {p: enactment['bindings'][p]
                                 for p in schema.parameters})
            self.send_q.put(m)
        except KeyError as e:
            logging.debug(
                "Missing parameter for sending {}: {}".format(schema.name, e))
            pass

    def forward(self, schema, recipient, enactment):
        m = Message(schema,
                    {p: enactment['bindings'][p]
                     for p in schema.parameters},
                    dest=self.configuration[recipient])
        self.send_q.put(m)

    def process_send(self, message):
        """
        Send a message by posting to the recipient's http endpoint,
        after checking for correctness, and storing the message.
        """

        if self.history.validate_send(message):
            if not self.history.duplicate(message):
                self.history.observe(message)

                logger.debug("Sending message {} to {} at {}".format(
                    message.payload, message.schema.recipient.name, message.dest))

                message.enactment = self.history.enactment(message)
                self.react(message)
            else:
                logger.debug("Resending message: {}".format(message))
                message.meta['retries'] = message.meta.get('retries', 0) + 1
                message.meta['last-retry'] = str(datetime.datetime.now())

            if not message.dest:
                message.dest = self.configuration[message.schema.recipient]
            self.emitter.send(message)
            return True

    def register_reactor(self, schema, handler):
        if self.reactors.get(schema):
            self.reactors[schema].add(handler)
        else:
            self.reactors[schema] = {handler}  # set

    def reaction(self, schema):
        """
        Decorator for declaring reactor handler.

        Example:
        @adapter.react(MessageSchema)
        def handle_message(message, enactment):
            'do stuff'
        """
        return partial(self.register_reactor, schema)

    def react(self, message):
        """
        Handle emission/reception of message by invoking corresponding reactors.
        """
        reactors = self.reactors.get(message.schema)
        if reactors:
            for r in reactors:
                logger.info("Invoking reactor: {}".format(r))
                # run reactor in a thread
                Thread(target=r, args=(message, self)).start()

    def process_loop(self):
        while True:
            # very busy waiting...
            if not self.send_q.empty():
                self.process_send(self.send_q.get())
            if not self.recv_q.empty():
                self.process_receive(self.recv_q.get())

    def start(self):
        self.process_thread.start()
        self.emitter.start()
        self.receiver.start(self)
        for s in self.schedulers:
            s.start(self)

    def add_policies(self, condition, *ps):
        if condition == 'reactive':
            for policy in ps:
                if type(policy) is str:
                    policy = policies.parse(self.protocol, policy)
                for schema, reactor in policy.reactors.items():
                    self.register_reactor(schema, reactor)
        else:
            s = Scheduler(condition)
            self.schedulers.append(s)
            for policy in ps:
                if type(policy) is str:
                    policy = policies.parse(self.protocol, policy)
                s.add(policy)

    def load_policies(self, spec):
        if type(spec) is str:
            spec = yaml.full_load(spec)
        if self.role.name in spec:
            for condition, ps in spec[self.role.name].items():
                self.add_policies(condition, *ps)
        else:
            print(self.role.name)
            # Assume the file contains policies only for agent
            for condition, ps in spec.items():
                self.add_policies(condition, *ps)

    def load_policy_file(self, path):
        with open(path) as file:
            spec = yaml.full_load(file)
            self.load_policies(spec)
