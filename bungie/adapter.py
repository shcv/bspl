import asyncio
import aiorun
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
from .scheduler import Scheduler, exponential
from .statistics import stats, increment
from . import policies

FORMAT = '%(asctime)-15s %(module)s: %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger('bungie')


def get_key(schema, payload):
    # schema.keys should be ordered, or sorted for consistency
    return ','.join(k + ':' + str(payload[k]) for k in schema.keys)


class Message:
    def __init__(self, schema, payload, duplicate=False, acknowledged=False, dest=None):
        self.schema = schema
        self.payload = payload
        self.duplicate = duplicate
        self.acknowledged = acknowledged
        self.dest = dest
        self.meta = {}

        self.key = get_key(self.schema, self.payload)

    def __repr__(self):
        if self.duplicate:
            return f"Message({self.schema.name}, {self.payload}, duplicate={self.duplicate})"
        else:
            return f"Message({self.schema.name}, {self.payload})"

    def __eq__(self, other):
        return self.payload == other.payload and self.schema == other.schema

    def __hash__(self):
        return hash(self.schema.qualified_name+self.key)

    def keys_match(self, other):
        return all(self.payload[k] == other.payload[k]
                   for k in self.schema.keys
                   if k in other.schema.parameters)

    def ack(self):
        payload = {k: self.payload[k] for k in self.schema.keys}
        payload['$ack'] = self.schema.name
        self.acknowledged = True
        schema = self.schema.acknowledgment()
        return Message(schema, payload)

    def project_key(self, schema):
        key = []
        # use ordering from other schema
        for k in schema.keys:
            if k in self.schema.keys:
                key.append(k)
        return ','.join(k + ':' + str(self.payload[k]) for k in key)


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
        self.signatures = {}
        self.history = History()
        self.emitter = emitter
        self.receiver = receiver or Receiver(self.configuration[self.role])
        self.schedulers = []

    async def receive(self, payload):
        if not isinstance(payload, dict):
            logger.warn(
                "Payload does not parse to a dictionary: {}".format(payload))
            return

        if '$ack' in payload:
            s = self.protocol.messages[payload['$ack']]
            k = get_key(s, payload)

            dup = self.history.acknowledge(s, k)

            if 'acks' not in stats:
                stats.update({'acks': 0, 'dup acks': 0})
            if not dup:
                stats['acks'] += 1
            else:
                stats['dup acks'] += 1

            await self.react(Message(s.acknowledgment(), payload))
            return

        schema = self.protocol.find_schema(payload, to=self.role)
        if not schema:
            logger.warn("No schema matching payload: {}".format(payload))
            return
        message = Message(schema, payload)
        message.meta['received'] = datetime.datetime.now()
        increment('receptions')
        if self.history.duplicate(message):
            logger.debug("Duplicate message: {}".format(message))
            increment('dups')
            message.duplicate = True
            await self.react(message)
        elif self.history.check_integrity(message):
            logger.debug("Observing message: {}".format(message))
            increment('observations')
            self.history.observe(message)
            await self.react(message)

    def send(self, payload, schema=None, name=None, to=None):
        schema = schema or self.protocol.find_schema(payload, name=name, to=to)
        m = Message(schema, payload)
        loop = asyncio.get_running_loop()
        loop.create_task(self.process_send(m))

    async def resend(self, schema, enactment):
        try:
            m = Message(schema, {p: enactment['bindings'][p]
                                 for p in schema.parameters})
            await self.process_send(m)
        except KeyError as e:
            logging.debug(
                "Missing parameter for sending {}: {}".format(schema.name, e))
            pass

    async def forward(self, schema, recipient, enactment):
        m = Message(schema,
                    {p: enactment['bindings'][p]
                     for p in schema.parameters},
                    dest=self.configuration[recipient])
        await self.process_send(m)

    async def process_send(self, message):
        if await self.prepare_send(message):
            await self.emitter.send(message)

    async def prepare_send(self, message):
        """
        Checking a message for correctness, and possibly store it.
        """

        if not message.dest:
            message.dest = self.configuration[message.schema.recipient]
        if '$ack' in message.payload:
            # don't need to observe ack messages
            return message
        if self.history.duplicate(message):
            logger.debug(f"Resending message: {message}")
            stats['retries'] = stats.get('retries', 0)+1
            message.meta['retries'] = message.meta.get('retries', 0) + 1
            stats['max retries'] = max(
                stats.get('max retries', 0), message.meta['retries'])
            message.meta['last-retry'] = datetime.datetime.now()
            return message
        elif self.history.validate_send(message):
            self.history.observe(message)
            await self.react(message)
            return message
        else:
            return False

    async def bulk_send(self, messages):
        if hasattr(self.emitter, 'bulk_send'):
            ms = await asyncio.gather(*[self.prepare_send(m) for m in messages])
            to_send = [m for m in ms if m]
            logger.debug(f'bulk sending {len(to_send)} messages')
            await self.emitter.bulk_send(to_send)
        else:
            for m in messages:
                if self.prepare_send(message):
                    await self.react(message)
                    await self.emitter.send(message)

    def register_reactor(self, schema, handler, index=None):
        if schema in self.reactors:
            rs = self.reactors[schema]
            if handler not in rs:
                rs.insert(index if index is not None else len(rs), handler)
                self.signatures[schema][handler] = inspect.signature(
                    handler).parameters
        else:
            self.reactors[schema] = [handler]
            self.signatures[schema] = {
                handler: inspect.signature(handler).parameters}

    def reaction(self, schema):
        """
        Decorator for declaring reactor handler.

        Example:
        @adapter.reaction(MessageSchema)
        def handle_message(message, enactment):
            'do stuff'
        """
        return partial(self.register_reactor, schema)

    async def react(self, message):
        """
        Handle emission/reception of message by invoking corresponding reactors.
        """
        reactors = self.reactors.get(message.schema)
        if reactors:
            enactment = self.history.enactment(message)
            for r in reactors:
                logger.debug("Invoking reactor: {}".format(r))
                await r(message, enactment, self)

    async def task(self):
        loop = asyncio.get_running_loop()

        if hasattr(self.receiver, 'task'):
            await self.receiver.task(self)
        if hasattr(self.emitter, 'task'):
            await self.emitter.task()
        for s in self.schedulers:
            loop.create_task(s.task(self))

    def add_policies(self, *ps, when='reactive'):
        for policy in ps:
            if type(policy) is str:
                policy = policies.parse(self.protocol, policy)
            for schema, reactor in policy.reactors.items():
                self.register_reactor(schema, reactor, policy.priority)
            if when != 'reactive':
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
        async def main():
            await self.task()
            loop = asyncio.get_running_loop()
            for t in tasks:
                loop.create_task(t)

        aiorun.run(main(), stop_on_unhandled_errors=True, use_uvloop=True)
