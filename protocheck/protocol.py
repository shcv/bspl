from .sat.logic import merge


class Specification():
    def __init__(self, protocols=None):
        self.protocols = {}  # name : protocol
        self.type = 'specification'
        if (protocols):
            self.add_protocols(protocols)

    def add_protocols(self, protocols=list()):
        # store protocol by name
        for p in protocols:
            self.protocols[p.name] = p

        for p in self.protocols.values():
            p.resolve_references(self)

    # @classmethod
    # def from_json(cls, protocols):
    #     return cls([Protocol.from_dict(p, self) for p in protocols])

    @property
    def messages(self):
        return set(m for p in self.protocols.values() for m in p.messages.values())


class Base():
    """Class containing elements common to protocols, messages, etc."""

    def __init__(self, name, parent, type):
        self.raw_name = name.strip()
        self.parent = parent
        self.type = type

    @property
    def qualified_name(self):
        return self.parent.name + "/" + self.raw_name

    @property
    def name(self):
        return self.raw_name

    # @classmethod
    # def from_dict(cls, data, parent=None):
    #     return cls(data["name"].strip(), parent, schema["type"])


class Role(Base):
    def __init__(self, name, parent=None):
        super().__init__(name, parent, "role")

    def messages(self, protocol):
        return {m.name: m for m in protocol.messages.values()
                if m.sender == self or m.recipient == self}

    def sent_messages(self, protocol):
        return [m for m in protocol.messages.values() if m.sender == self]


class Reference(Base):
    def __init__(self, name, parameters=None, parent=None):
        self.parameters = parameters  # list(Parameter)
        super().__init__(name, parent, "reference")

    def format(self, ref=True):
        return "{}({}, {})".format(self.name,
                                   ", ".join([r.name for r in self.roles]),
                                   ", ".join([p.format() for p in self.parameters]))


class Protocol(Base):
    def __init__(self,
                 name,
                 roles=None,
                 public_parameters=None,
                 references=None,
                 parent=None,
                 private_parameters=None,
                 ):
        super().__init__(name, parent, "protocol")
        self.public_parameters = {}
        self.private_parameters = {}
        self.roles = {}
        self.references = {}
        self.configure(roles, public_parameters,
                       references, private_parameters)

    def configure(self,
                  roles=None,
                  public_parameters=None,
                  references=None,
                  private_parameters=None,
                  parent=None):
        parent = self.parent = getattr(self, 'parent', parent)
        if roles:
            self.roles = {r.name: r for r in roles or []}
        if public_parameters:
            self.set_parameters(public_parameters or [])
            self.keys = {p.name for p in self.parameters.values()
                         if p.key
                         or parent
                         and parent.type == 'protocol'
                         and p.name in parent.parameters
                         and parent.parameters[p.name].key}
        if private_parameters:
            self.private_parameters = {p.name: p for p in private_parameters}
        if references:
            self.references = {r.name: r for r in references or []}

    def set_parameters(self, parameters):
        self.public_parameters = {p.name: p for p in parameters}

    @property
    def parameters(self):
        if hasattr(self, 'private_parameters'):
            return merge(self.public_parameters, self.private_parameters)
        else:
            return self.public_parameters

    @property
    def all_parameters(self):
        return {p for m in self.messages.values() for p in m.parameters}

    def _adorned(self, adornment):
        "helper method for selecting parameters with a particular adornment"
        return {p.name for p in self.public_parameters.values()
                if p.adornment == adornment}

    @property
    def ins(self):
        return self._adorned('in')

    @property
    def outs(self):
        return self._adorned('out')

    @property
    def nils(self):
        return self._adorned('nil')

    @property
    def messages(self):
        return {k: v for r in self.references.values() for k, v in r.messages.items()}

    @property
    def is_entrypoint(self):
        "A protocol is an entry point if it does not have any \
        dependencies on sibling protocols"
        return not self.ins - self.parent.ins

    def format(self, ref=False):
        if ref:
            return "{}({}, {})".format(self.name,
                                       ", ".join(self.roles),
                                       ", ".join([p.format() for p in self.public_parameters.values()]))
        else:
            return """{} {{
  roles {}
  parameters {}
{}
  {}
}}""".format(self.name,
             ", ".join(self.roles.keys()),
             ", ".join([p.format() for p in self.public_parameters.values()]),
             "  private " +
             ", ".join([p for p in self.private_parameters]) +
             "\n" if self.private_parameters else "",
             "\n  ".join([r.format(ref=True) for r in self.references.values()]))

    def to_dict(self):
        data = {
            "name": self.name,
            "type": self.type,
            "parameters": [p for p in self.public_parameters.keys()],
            "keys": [k for k in self.keys],
            "ins": [i for i in self.ins],
            "outs": [i for i in self.outs],
            "nils": [i for i in self.nils],
        }
        if self.roles:
            data["roles"] = [r for r in self.roles.keys()]
        # should we output references, or just flatten to messages?
        if self.referegnces:
            data["messages"] = {r.name: r.to_dict()
                                for r in self.messages.values()}
        return data

    def projection(protocol, role):
        references = [
            r for r in protocol.references if role in r.roles.values()
            or r.type == 'message' and (role == r.sender or role == r.recipient)]

        messages = [m for m in references if m.type == 'message']

        if len(messages) > 0:
            return Protocol(
                protocol.name,
                public_parameters=[p for p in protocol.public_parameters.values()
                                   if any(p.name in m.parameters for m in messages)],
                private_parameters=[p for p in protocol.private_parameters.values()
                                    if any(p.name in m.parameters for m in messages)],
                roles=[r for r in protocol.roles
                       if any(m.sender.name == r.name
                              or m.recipient.name == r.name
                              for m in messages)],
                references=[r.schema for r in references],
                parent=protocol.parent)

    def resolve_references(self, spec):
        refs = {}
        for r in self.references.values():
            protocol = spec.protocols.get(r.name)
            if protocol:
                refs[r.name] = protocol.instance(spec, self, r)
            else:
                refs[r.name] = r.instance(self)
        self.references = refs

    def instance(self, spec, parent, reference):
        p = Protocol(self.name,
                     self.roles.values(),
                     public_parameters=self.public_parameters.values(),
                     private_parameters=self.private_parameters.values(),
                     references=self.references.values(),
                     parent=parent)
        for i, r in enumerate(self.roles.values()):
            p.roles[r.name] = parent.roles.get(
                reference.parameters[i].name)
        for i, par in enumerate(self.public_parameters.values()):
            p.public_parameters[par.name].raw_name = \
                reference.parameters[i+len(p.roles)].name
        p.resolve_references(spec)
        return p

    def find_schema(self, payload, name=None, to=None):
        for schema in self.messages.values():
            if name and schema.name is not name:
                continue
            if to and schema.recipient is not to:
                continue
            # find schema with exactly the same parameters (except nils, which should not be bound)
            if not set(schema.ins).union(schema.outs).symmetric_difference(payload.keys()):
                return schema


class Message(Protocol):
    def __init__(self, name, sender=None, recipient=None, parameters=None, parent=None):
        if (sender and recipient):
            super(Protocol, self).__init__(name, parent=parent, type="message")
            self.configure(sender, recipient, parameters, parent)
        else:
            super(Protocol, self).__init__(name, parent=parent, type="message")

    def configure(self, sender=None, recipient=None, parameters=None, parent=None):
        self.idx = 1

        parent = parent or getattr(self, 'parent', None)
        if parent:
            self.sender = parent.roles.get(sender) \
                or parent.roles.get(getattr(sender, 'name', None))
            self.recipient = parent.roles.get(recipient) \
                or parent.roles.get(getattr(recipient, 'name', None))
            for p in parameters or []:
                if p.name not in parent.parameters:
                    raise LookupError("Undeclared parameter", p)
                elif parent.parameters[p.name].key:
                    p.key = True
        else:
            self.sender = sender if isinstance(
                sender, Role) else Role(sender, self)
            self.recipient = recipient if isinstance(
                recipient, Role) else Role(recipient, self)

        if not self.sender:
            raise LookupError("Role not found", sender, self.name, parent)
        if not self.recipient:
            raise LookupError("Role not found", recipient, self.name, parent)

        super().configure(roles=[self.sender, self.recipient],
                          public_parameters=parameters,
                          parent=parent)

    @property
    def qualified_name(self):
        return self.parent.name + "/" + self.name

    @property
    def name(self):
        return self.raw_name + (str(self.idx) if self.idx > 1 else "")

    def instance(self, parent):
        msg = Message(self.raw_name,
                      self.sender,
                      self.recipient,
                      self.parameters.values(),
                      parent)

        # handle duplicates
        for m in parent.references.values():
            if m == self:
                break
            if m.name == self.name:
                msg.idx += 1

        # propagate renaming from parent protocol
        for i, par in enumerate(self.public_parameters.values()):
            msg.public_parameters[par.name].raw_name = \
                parent.parameters[par.name].name

        return msg

    @property
    def messages(self):
        return {self.name: self}

    def format(self, ref=False):
        return "{} -> {}: {}[{}]".format(self.sender.name,
                                         self.recipient.name,
                                         self.name,
                                         ', '.join([p.format() for p in self.parameters.values()]))

    def to_dict(self):
        data = super(Message, self).to_dict()
        data["to"] = self.recipient.name
        data["from"] = self.sender.name
        return data


class Parameter(Base):
    def __init__(self, name, adornment, key=False, parent=None):
        self.adornment = adornment
        self.key = key
        super().__init__(name, parent, "parameter")

    def format(self, adornment=True):
        if adornment:
            base = "{} {}".format(self.adornment, self.name)
        else:
            base = "{}".format(self.name)

        if self.key:
            return base + " key"
        else:
            return base
