#!/usr/bin/env python3

import agentspeak
import agentspeak.runtime
import agentspeak.stdlib
import asyncio
import uuid

from agentspeak import Actions
from agentspeak.runtime import Agent


class Environment(agentspeak.runtime.Environment):
    async def task(self, adapter):
        """Async alternative to Environment.run() so BDI processing can run alongside protocol adapter"""
        self.adapter = adapter
        self.wake_signal = asyncio.Event()

        # add an outer loop to wake up environment for an external event
        while self.adapter.running:
            await self.loop()
            await self.wake_signal.wait()

    async def loop(self):
        self.wake_signal.clear()
        maybe_more_work = True
        while maybe_more_work:
            maybe_more_work = False
            for agent in self.agents.values():
                if agent.step():
                    maybe_more_work = True

            if not maybe_more_work:
                deadlines = (
                    agent.shortest_deadline() for agent in self.agents.values()
                )
                deadlines = [deadline for deadline in deadlines if deadline is not None]
                if deadlines:
                    await asyncio.sleep(min(deadlines) - self.time())
                    maybe_more_work = True


class Agent(agentspeak.runtime.Agent):
    def bind(self, adapter):
        """For late binding"""
        self.adapter = adapter


actions = Actions(agentspeak.stdlib.actions)

actions.add_function(".uuid", (), lambda: str(uuid.uuid4()))


@actions.add_procedure(".emit", (agentspeak.runtime.Agent, str, tuple))
def emit(agent, name, parameters):
    # resolve literals to be serializeable
    params = [
        p if not isinstance(p, agentspeak.Literal) else p.asl_repr() for p in parameters
    ]
    # Find schema using name
    schema = agent.adapter.protocol.find_schema(name=name)
    # Construct payload using parameter list
    payload = schema.zip_params(*params)
    # Attempt emission
    agent.adapter.send(payload, schema=schema)
