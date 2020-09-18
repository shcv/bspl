import asyncio
import logging
import json
import datetime
import sys
import os
import math
import socket
import inspect
import yaml
from asyncio.queues import Queue
from .history import History
from functools import partial
from .emitter import Emitter
from .receiver import Receiver
from .scheduler import Scheduler
from . import policies

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger('bungie')


class Message:
    def __init__(self, schema, payload, duplicate=False, acknowledged=False, dest=None):
        self.schema = schema
        self.payload = payload
        self.duplicate = duplicate
        self.acknowledged = acknowledged
        self.dest = dest
        self.meta = {}

    def __repr__(self):
        if self.duplicate:
            return f"Message({self.schema.name}, {self.payload}, duplicate={self.duplicate})"
        else:
            return f"Message({self.schema.name}, {self.payload})"

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

    def ack(self):
        payload = {k: self.payload[k] for k in self.schema.keys}
        payload['$ack'] = self.schema.name
        self.acknowledged = True
        return Message(self.schema.parent.messages['@'+self.schema.name], payload)


class Adapter:
    def __init__(self,
                 role,
                 protocol,
                 configuration,
                 emitter=Emitter(),
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
        self.reactors = {}  # dict of message -> [handlers]
        self.history = History()
        self.emitter = emitter
        self.receiver = receiver or Receiver(self.configuration[self.role])
        self.schedulers = []

    async def process_receive(self, payload):
        if not isinstance(payload, dict):
            logger.warn(
                "Payload does not parse to a dictionary: {}".format(payload))
            return

        schema = self.protocol.find_schema(payload, to=self.role)
        if not schema:
            logger.warn("No schema matching payload: {}".format(payload))
            return
        elif '$ack' in payload:
            # look up message schema by name
            s = self.protocol.messages[payload['$ack']]
            m = Message(s, payload)
            self.history.acknowledge(m)
        message = Message(schema, payload)
        enactment = self.history.check_integrity(message)
        if enactment is not False:
            if self.history.duplicate(message):
                logger.debug("Duplicate message: {}".format(message))
                message.duplicate = True
            else:
                logger.debug("Observing message: {}".format(message))
                self.history.observe(message)

            await self.react(message, enactment)

    def send(self, payload, schema=None, name=None, to=None):
        """
        Add a message to the outgoing queue
        """
        schema = schema or self.protocol.find_schema(payload, name=name, to=to)
        m = Message(schema, payload)
        loop = asyncio.get_running_loop()
        loop.create_task(self.send_q.put(m))

    async def resend(self, schema, enactment):
        try:
            m = Message(schema, {p: enactment['bindings'][p]
                                 for p in schema.parameters})
            await self.send_q.put(m)
        except KeyError as e:
            logging.debug(
                "Missing parameter for sending {}: {}".format(schema.name, e))
            pass

    async def forward(self, schema, recipient, enactment):
        m = Message(schema,
                    {p: enactment['bindings'][p]
                     for p in schema.parameters},
                    dest=self.configuration[recipient])
        await self.send_q.put(m)

    async def process_send(self, message):
        """
n        Send a message by posting to the recipient's http endpoint,
        after checking for correctness, and storing the message.
        """

        if not message.dest:
            message.dest = self.configuration[message.schema.recipient]
        if not self.history.duplicate(message):
            if self.history.validate_send(message):
                self.history.observe(message)

                logger.debug("Sending message {} to {} at {}".format(
                    message.payload, message.schema.recipient.name, message.dest))

                enactment = self.history.enactment(message)
                await self.react(message, enactment)

                self.emitter.send(message)
                return True
        else:
            logger.debug(f"Resending message: {message}")
            message.meta['retries'] = message.meta.get('retries', 0) + 1
            message.meta['last-retry'] = str(datetime.datetime.now())

            self.emitter.send(message)
            return True

    def register_reactor(self, schema, handler, index=None):
        if schema in self.reactors:
            rs = self.reactors[schema]
            if handler not in rs:
                rs.insert(index if index is not None else len(rs), handler)
        else:
            self.reactors[schema] = [handler]

    def reaction(self, schema):
        """
        Decorator for declaring reactor handler.

        Example:
        @adapter.react(MessageSchema)
        def handle_message(message, enactment):
            'do stuff'
        """
        return partial(self.register_reactor, schema)

    async def react(self, message, enactment):
        """
        Handle emission/reception of message by invoking corresponding reactors.
        """
        reactors = self.reactors.get(message.schema)
        if reactors:
            loop = asyncio.get_running_loop()
            for r in reactors:
                logger.info("Invoking reactor: {}".format(r))
                # run reactors asynchronously
                loop.create_task(r(message, enactment, self))

    async def task(self):
        loop = asyncio.get_running_loop()
        self.send_q = Queue()
        self.recv_q = Queue()

        async def send_loop():
            while True:
                m = await self.send_q.get()
                await self.process_send(m)

        async def receive_loop():
            while True:
                m = await self.recv_q.get()
                await self.process_receive(m)

        loop.create_task(self.receiver.task(self))
        loop.create_task(receive_loop())
        loop.create_task(self.emitter.task())
        loop.create_task(send_loop())
        for s in self.schedulers:
            loop.create_task(s.task(self))

    def add_policies(self, *ps, when='reactive'):
        for policy in ps:
            if type(policy) is str:
                policy = policies.parse(self.protocol, policy)
            if when == 'reactive':
                for schema, reactor in policy.reactors.items():
                    self.register_reactor(schema, reactor, policy.priority)
            else:
                s = Scheduler(when)
                self.schedulers.append(s)
                s.add(policy)

    def load_policies(self, spec):
        if type(spec) is str:
            spec = yaml.full_load(spec)
        if self.role.name in spec:
            for condition, ps in spec[self.role.name].items():
                self.add_policies(*ps, when=condition)
        else:
            # Assume the file contains policies only for agent
            for condition, ps in spec.items():
                self.add_policies(*ps, when=condition)

    def load_policy_file(self, path):
        with open(path) as file:
            spec = yaml.full_load(file)
            self.load_policies(spec)

    def start(self, *tasks):
        loop = asyncio.get_event_loop()

        loop.create_task(self.task())
        for t in tasks:
            loop.create_task(t)
        loop.run_forever()
