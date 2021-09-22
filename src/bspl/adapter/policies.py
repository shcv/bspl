import yaml
import tatsu
import os
import logging
import datetime
import uuid

logger = logging.getLogger("bungie.policies")
logger.setLevel(logging.DEBUG)


def autoincrement(parameter):
    def _autoinc(context):
        current = 0
        for m in context.messages:
            current = max(current, m.payload.get(parameter))
        return current + 1

    return _autoinc


def guid():
    return str(uuid.uuid4())


generators = {"autoincrement": autoincrement, "guid": guid}


def map_message(map, kind, m):
    return map[kind][m.schema][0](**m.payload, **{map[kind][m.schema][1]: guid()})


def map_messages(map, kind, messages):
    for m in messages:
        yield map_message(map, kind, m)


grammar_path = os.path.join(os.path.dirname(__file__), "policy.gr")
with open(grammar_path, "r", encoding="utf8") as grammar:
    model = tatsu.compile(grammar.read())


def lookup(protocol, names):
    return [protocol.messages[name] for name in names]


def from_ast(protocol, ast):
    action = ast.get("action")
    cls = {
        "remind": Remind,
        "forward": Forward,
        "send": Send,
        "acknowledge": Acknowledge,
    }.get(action["verb"])

    policy = cls(*lookup(protocol, action["messages"]))

    if ast.get("delay"):
        policy.after(float(ast["delay"]))

    if ast.get("prep"):
        if ast["prep"] == "until":
            policy.until
        elif ast["prep"] == "upon":
            policy.upon
        else:
            raise Exception("Unknown preposition: {}".format(ast["prep"]))

    def add_event(event):
        if type(event) is tuple:
            if event[0] == "or":
                policy.Or
            elif event[0] == "and":
                policy.And
            else:
                raise Exception("Unknown conjunction: {}".format(event[0]))

            for e in event[1:]:
                add_event(e)
            return

        kind = event["type"]
        messages = lookup(protocol, event["messages"])
        if kind == "received":
            policy.received(*messages)
        elif kind == "acknowledged":
            policy.acknowledged

    if ast.get("events"):
        add_event(ast["events"])

    return policy


def parse(protocol, text):
    policies = yaml.full_load(text)
    for p in policies:
        p["policy"] = from_ast(protocol, model.parse(p["policy"]))
    return policies


class Acknowledge:
    def __init__(self, *schemas):
        self.schemas = schemas
        self.reactive = True
        self.priority = 0

    def With(self, schema, key):
        self.ack = (schema, key)
        return self

    def Map(self, map):
        self.map = map
        return self

    @property
    def reactors(self):
        async def ack(message):
            if hasattr(self, "map"):
                m = map_message(self.map, "acknowledgments", message)
            elif hasattr(self, "ack"):
                m = self.ack[0](**message.payload, **{self.ack[1]: guid()})
            else:
                logging.error(
                    f"Need to configure acknowledgment mapping for message: {message}"
                )
            await message.adapter.process_send(m)

        return {s: ack for s in self.schemas}


class Remind:
    """
    A helper class for defining remind policies.

    The following statement returns a function that returns a list of all Accept messages that do not have corresponding Deliver instances in the history.
      Remind(Accept).until.received(Deliver)

    Other example policies:

      Remind(Accept).until.acknowledged(Accept)
    """

    def __init__(self, *schemas):
        """List of message schemas to try reminding"""
        self.schemas = schemas
        self.reactors = {}
        self.reactive = False
        self.disjunctive = True
        self.proactors = []
        self.priority = None
        self.delay = None
        self.generators = {}
        self.map = {}
        self.key = "reminders"

        # the set of active messages, for proactive policies
        self.active = set()

    def run(self, history):
        selected = set()
        first = True
        for p in self.proactors:
            if first:
                selected = p(history)
                continue
            if self.disjunctive:
                selected.update(p(history))
            else:
                selected.intersection_update(p(history))
        return selected

    async def action(self, adapter, schema, context):
        # remind message
        for m in context.messages:
            if m.schema == schema:
                reminder = map_message(self.map, self.key, m)
                adapter.send(reminder)

    def With(self, map):
        self.map = map
        return self

    def after(self, delay):
        self.delay = delay
        return self

    @property
    def until(self):
        self.reactive = False
        return self

    def received(self, *expectations):
        """
        Select messages for which not all of the listed expectations have been received.
        E.g.:
          Remind(A).until.received(B,C)
        will remind A until /both/ B and C are received.

        To handle a disjunction, use separate received() clauses and at least one Or.
        E.g.:
          Remind(A).until.received(B).Or.received(C)
        """

        if self.reactive:
            for s in expectations:

                async def reactor(msg):
                    context = msg.adapter.history.context(msg)
                    for r in self.schemas:
                        # remind message schema r in the same context as msg
                        await self.action(msg.adapter, r, context)

                self.reactors[s] = reactor
        else:

            async def activate(message):
                message.meta["sent"] = datetime.datetime.now()
                self.active.add(message)

            for s in self.schemas:
                self.reactors[s] = activate

            async def deactivate(message):
                for s in self.schemas:
                    m = message.adapter.history.find_context(
                        **message.project_key(s)
                    ).find(s)
                    if m and m in self.active:
                        self.active.remove(m)

            for e in expectations:
                self.reactors[e] = deactivate

            def process(history):
                messages = []
                if not self.delay:
                    for m in self.active:
                        reminder = map_message(self.map, self.key, m)
                        messages.append(reminder)
                        if len(messages) >= 500:
                            break
                else:
                    now = datetime.datetime.now()
                    i = 0
                    for m in self.active:
                        if (now - m.meta["sent"]).total_seconds() >= self.delay:
                            i += 1
                            messages.append(map_message(self.map, self.key, m))
                        if i >= 500:
                            break
                logger.debug(f"Sending {len(messages)} reminders")
                return messages

            self.proactors.append(process)
        return self

    @property
    def Or(self):
        self.disjunctive = True
        return self

    @property
    def And(self):
        self.disjunctive = False
        return self

    @property
    def acknowledged(self):
        """
        If proactive, add a process to the policy to remind the messages until they are acknowledged.
        Example:
          Remind(Accept).until.acknowledged
        """

        if self.reactive:
            pass
        else:

            async def activate(message):
                message.meta["sent"] = datetime.datetime.now()
                self.active.add(message)

            for m in self.schemas:
                self.reactors[m] = activate

            def gen_deactivate(schema):
                async def deactivate(message):
                    m = message.adapter.history.find_context(
                        **message.project_key(schema)
                    ).find(schema)
                    if m and m in self.active:
                        self.active.remove(m)

                return deactivate

            for s in self.schemas:
                self.reactors[self.map["acknowledgments"][s][0]] = gen_deactivate(s)

            def process_acknowledged(history):
                if not self.delay:
                    messages = self.active
                    return map_messages(self.map, "forwards", messages)
                else:
                    now = datetime.datetime.now()
                    messages = []
                    i = 0
                    for m in self.active:
                        if (now - m.meta["sent"]).total_seconds() >= self.delay:
                            messages.append(m)
                    return map_messages(self.map, "forwards", messages)

            self.proactors.append(process_acknowledged)
        return self

    @property
    def upon(self):
        self.reactive = True
        return self


class Forward(Remind):
    """
    Forwarding policy; sends a message to a specified recipient.
    E.g.: Forward(Deliver).to(Seller).upon.received(Deliver)
    """

    def __init__(self, *schemas):
        super().__init__(*schemas)
        self.recipient = None
        self.key = "forwards"
        self.reactive = True

    def to(self, recipient):
        self.recipient = recipient
        return self

    def observed(self, *schemas):
        return self.received(*schemas)


Send = Forward  # alias
