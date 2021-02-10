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
from types import MethodType
from asyncio.queues import Queue
from .history import History, Message
from functools import partial
from .emitter import Emitter
from .receiver import Receiver
from .scheduler import Scheduler, exponential
from .statistics import stats, increment
from . import policies

FORMAT = "%(asctime)-15s %(module)s: %(message)s"
logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger("bungie")


class Adapter:
    def __init__(self, role, protocol, configuration, emitter=Emitter(), receiver=None):
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

        self.inject(protocol)

    def inject(self, protocol):
        """Install helper methods into schema objects"""

        def match(schema, **params):
            """Construnct instances of schema that match params"""
            # identify keys
            # search history for objects that match keys
            print(f"you asked {schema} to match {params}")

        for m in protocol.messages.values():
            m.match = MethodType(match, m)

    async def receive(self, payload):
        if not isinstance(payload, dict):
            logger.warn("Payload does not parse to a dictionary: {}".format(payload))
            return

        schema = self.protocol.find_schema(payload, to=self.role)
        if not schema:
            logger.warn("No schema matching payload: {}".format(payload))
            return
        message = Message(schema, payload)
        message.meta["received"] = datetime.datetime.now()
        increment("receptions")
        if self.history.duplicate(message):
            logger.debug("Duplicate message: {}".format(message))
            increment("dups")
            # Don't react to duplicate messages
            # message.duplicate = True
            # await self.react(message)
        elif self.history.check_integrity(message):
            logger.debug("Observing message: {}".format(message))
            increment("observations")
            self.history.observe(message)
            await self.react(message)

    def send(self, payload, schema=None, name=None, to=None):
        if isinstance(payload, Message):
            m = payload
        else:
            schema = schema or self.protocol.find_schema(payload, name=name, to=to)
            m = Message(schema, payload)

        loop = asyncio.get_running_loop()
        loop.create_task(self.process_send(m))

    def fill(self, schema, enactment):
        bindings = enactment.bindings
        payload = {}
        for p in scehma.parameters:
            if p in self.generators:
                payload[p] = self.generators[p](enactment)
            elif p in bindings:
                payload[p] = bindings[p]
            else:
                logging.debug(f"Missing parameter for {schema.name}: {e}")
                return
        return Message(schema, payload)

    async def process_send(self, message):
        if await self.prepare_send(message):
            await self.emitter.send(message)

    async def prepare_send(self, message):
        """
        Checking a message for correctness, and possibly store it.
        """

        # if not message.schema.validate(message.payload):
        #     logger.warn(f'Invalid payload: {message.payload}')
        if not message.dest:
            message.dest = self.configuration[message.schema.recipient]
        if self.history.duplicate(message):
            logger.debug(f"Skipping duplicate message: {message}")
            # stats['retries'] = stats.get('retries', 0)+1
            # message.meta['retries'] = message.meta.get('retries', 0) + 1
            # stats['max retries'] = max(
            #    stats.get('max retries', 0), message.meta['retries'])
            # message.meta['last-retry'] = datetime.datetime.now()
            # return message
            return False
        elif self.history.validate_send(message):
            self.history.observe(message)
            await self.react(message)
            return message
        else:
            return False

    async def bulk_send(self, messages):
        if hasattr(self.emitter, "bulk_send"):
            ms = await asyncio.gather(*[self.prepare_send(m) for m in messages])
            to_send = [m for m in ms if m]
            logger.debug(f"bulk sending {len(to_send)} messages")
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
                self.signatures[schema][handler] = inspect.signature(handler).parameters
        else:
            self.reactors[schema] = [handler]
            self.signatures[schema] = {handler: inspect.signature(handler).parameters}

    def register_reactors(self, handler, schemas=[]):
        for s in schemas:
            self.register_reactor(s, handler)

    def reaction(self, *schemas):
        """
        Decorator for declaring reactor handler.

        Example:
        @adapter.reaction(MessageSchema)
        def handle_message(message):
            'do stuff'
        """
        return partial(self.register_reactors, schemas=schemas)

    async def react(self, message):
        """
        Handle emission/reception of message by invoking corresponding reactors.
        """
        reactors = self.reactors.get(message.schema)
        if reactors:
            for r in reactors:
                logger.debug("Invoking reactor: {}".format(r))
                message.adapter = self
                await r(message)

    async def task(self):
        loop = asyncio.get_running_loop()

        if hasattr(self.receiver, "task"):
            await self.receiver.task(self)
        if hasattr(self.emitter, "task"):
            await self.emitter.task()
        for s in self.schedulers:
            loop.create_task(s.task(self))

    def add_policies(self, *ps, when="reactive"):
        for policy in ps:
            # action = policy.get('action')
            # if type(action) is str:
            #     action = policies.parse(self.protocol, action)
            for schema, reactor in policy.reactors.items():
                self.register_reactor(schema, reactor, policy.priority)
            if when != "reactive":
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
