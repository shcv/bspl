import asyncio
from bspl.adapter import Adapter
from bspl.adapter.message import Message
from bspl.adapter.jason import actions, agentspeak
from bspl.utils import upcamel

from configuration import systems, agents


@actions.add(".emitAll", 1)
def emit(agent, term, intention):
    """
    emitAll/1 sends a message represented by a single term to all systems
    """
    message = agentspeak.evaluate(term.args[0], intention.scope)
    args = [agentspeak.evaluate(p, intention.scope) for p in message.args]
    name = message.functor
    # don't need system
    # system = args[0]
    sender = args[1]
    recipient = args[2]
    parameters = args[3:]

    # resolve literals to be serializeable
    params = [
        p if not isinstance(p, agentspeak.Literal) else p.asl_repr() for p in parameters
    ]

    for system in agent.adapter.systems:
        # Find schema using name
        schema = agent.adapter.systems[system]["protocol"].find_schema(
            name=upcamel(name)
        )
        # Construct payload using parameter list
        payload = schema.zip_params(*params)

        m = Message(schema, payload, system=system)

        if isinstance(recipient, str) and ":" in recipient:
            addr, port = recipient.split(":")
            m.dest = (addr, int(port))

        asyncio.create_task(agent.adapter.send(m))
    yield


adapter = Adapter("Pnin", systems, agents)
adapter.load_asl("pnin.asl")

if __name__ == "__main__":
    print("Starting Pnin...")
    adapter.start()
