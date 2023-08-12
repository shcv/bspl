#!/usr/bin/env python3

from itertools import chain, product
from functools import reduce, partial
from .protocol import Protocol, Role, Parameter, Message
import re
from pathlib import Path
from .parsers.langshaw import load


def apply(a, f):
    return f(a)


def get_clause(spec, kind):
    for c in spec:
        if kind in c:
            return c[kind]
    return []


def delegates(parameter):
    """Returns the name of the parameter being delegated by the argument
    e.g. delegates("item@S") == "item"
    """
    m = re.match(r"(.*)@.*", parameter)
    if m:
        return m.groups()[0]


def delegates_to(parameter):
    """Returns the role being delegated to by the argument
    e.g. delegates("item@S") == "S"
    """
    m = re.match(r".*@(.*)", parameter)
    if m:
        return m.groups()[0]


def some(f):
    def wrap(v):
        # only call f on v if v is not None
        if v != None:
            return f(v)

    return wrap


def not_nil(*params):
    def inner(s):
        if not any(p[1] == "nil" for p in s if p[0] in params):
            return s

    return some(inner)


def delegation_role_alignment(role):
    "Only pass schemas with 'in' delegations, if the sender is the role delegated to"

    def inner(s):
        for p in s:
            if delegates(p[0]) and delegates_to(p[0]) != role and p[1] == "in":
                return
        return s

    return some(inner)


def getp(name, schema):
    "find parameter in schema by name"
    return next((p for p in schema if p[0] == name), None)


@some
def delegation_out_parameter_nil(s):
    "If a delegation is out, the parameter must be nil"
    ds = {p[0]: delegates(p[0]) for p in s if delegates(p[0])}
    for d in ds:
        if getp(d, s)[1] == "out" and getp(ds[d], s)[1] != "nil":
            return
    return s


def handle_delegation(role):
    "Schema receiving delegation must bind or re-delegate"

    def inner(s):
        d_self = {
            p[0]: delegates(p[0])
            for p in s
            if delegates(p[0]) and delegates_to(p[0]) == role
        }
        d_other = {
            # index by delegated parameter
            delegates(p[0]): p[0]
            for p in s
            # only include active delegations to other roles
            if delegates(p[0]) and delegates_to(p[0]) != role and p[1] == "out"
        }
        for d in d_self:
            direction = getp(d, s)[1]
            if direction == "out":
                return  # can't delegate to self
            elif direction == "in":
                # received delegation
                # must bind or delegate
                p = d_self[d]
                bound = getp(p, s)[1] == "out"
                if not bound and p not in d_other:
                    return

        return s

    return some(inner)


def ensure_priority(protocol, role):
    """
    Ensure that schemas reflect the priority of the actor.
    If the actor is not first, it may only bind or delegate if it has been delegated to.
    """

    def inner(s):
        for p in s:
            if protocol.can_be_delegated(role, p[0]):
                # not the first priority
                d_in = f"{p[0]}@{role}"
                if getp(d_in, s)[1] != "in":
                    # didn't receive delegation
                    to = protocol.delegates_to(role, p[0])
                    d_out = f"{p[0]}@{to}"
                    if (to and getp(d_out, s)[1] == "out") or getp(p[0], s)[1] == "out":
                        # can't delegate or bind
                        return
        return s

    return some(inner)


@some
def ensure_sayso(s):
    "Only pass schemas if there are no parameters that are nil but not delegated"
    for p in s:
        if (
            not delegates(p[0])  # p is not a delegation
            and p[1] == "nil"  # p is nil
            and all(  # all parameters delegating p are nil
                d[1] == "nil" for d in s if delegates(d[0]) == p[0]
            )
        ):
            return
    return s


def handle_exclusivity(protocol, role):
    "If a role has exclusive sayso for a parameter, and it only appears in one message, it must be out"

    def inner(s):
        for p in s:
            ps = protocol.priorities(p[0])
            if role in ps and len(ps) == 1:
                actions = [
                    a
                    for a in protocol.actions
                    if any(ap == p[0] and a.actor == role for ap in a.parameters)
                ]
                if len(actions) == 1:
                    if getp(p[0], s)[1] != "out":
                        return
        return s

    return some(inner)


def out_keys(keys):
    def inner(s):
        if not (
            # all keys out
            all(p[1] == "out" for p in s if p[0] in keys)
            # some parmeter in
            and any(p[1] == "in" for p in s if p[0] not in keys)
        ):
            return s

    return some(inner)


class Action:
    def __init__(self, spec, parent):
        self.spec = spec
        self.parent = parent

        self.actor = spec["actor"]
        self.name = spec["name"]
        self.parameters = spec["parameters"]

    @property
    def keys(self):
        return [p for p in self.parameters if p in self.parent.keys]

    @property
    def non_keys(self):
        return [p for p in self.parameters if p not in self.parent.keys]

    @property
    def delegations(self):
        """Returns a sequence of delegations for this action, where a
        delegation is a name of the form 'parameter@role'
        """
        for p in self.non_keys:
            if self.parent.can_be_delegated(self.actor, p):
                yield f"{p}@{self.actor}"
            to = self.parent.delegates_to(self.actor, p)
            if to:
                yield f"{p}@{to}"

    @property
    def autonomy_parameter(self):
        return self.name

    @property
    def expanded_parameters(self):
        yield from self.keys
        for p in self.non_keys:
            yield from self.parent.delegations(self.actor, p)
            yield p
        yield self.autonomy_parameter

    def possibilities(self, parameter):
        if parameter in self.keys:
            # keys can't be nil
            return ["in", "out"]
        elif parameter == self.autonomy_parameter:
            # autonomy parameter for this action is always out
            return ["out"]
        elif parameter in [a.name for a in self.parent.actions]:
            # autonomy parameters for other actions are always in
            return ["in"]
        elif self.parent.can_bind(self.actor, parameter):
            # if the actor can bind the parameter, it can be anything
            return ["in", "out", "nil"]
        else:
            return ["in", "nil"]

    def columns(self):
        for p in self.expanded_parameters:
            yield product([p], self.possibilities(p))

    def all_schemas(self):
        return product(*self.columns())

    def schemas(self):
        return filter(
            # call each filter function on s
            # each function passes it on if it succeeds the test
            # but short-circuits if passed None
            lambda s: reduce(
                apply,
                [
                    delegation_role_alignment(self.actor),
                    delegation_out_parameter_nil,
                    handle_delegation(self.actor),
                    ensure_sayso,
                    out_keys(self.keys),
                    handle_exclusivity(self.parent, self.actor),
                    ensure_priority(self.parent, self.actor),
                ],
                s,
            ),
            self.all_schemas(),
        )


def parameters(spec):
    return [p["name"] for pc in get_clause(spec, "what") for p in pc]


def validate(spec):
    # ensure there aren't multiple sayso clauses involving the same parameters
    for p in parameters(spec):
        clauses = [s for s in get_clause(spec, "sayso") if p in s["parameters"]]
        if len(clauses) > 1:
            clauses = "\n  ".join(map(str, clauses))
            raise Exception(
                f"Parameter {p} should only appear in one sayso clause:\n  {clauses}"
            )
    return True


class Langshaw:
    def __init__(self, spec):
        self.source = spec
        if isinstance(spec, str):
            spec = load(spec)
        validate(spec)
        self.spec = spec
        self.actions = [Action(a, self) for a in self.get_clause("actions")]
        self.autonomy_parameters = set()

    @classmethod
    def load_file(cls, path):
        source = Path(path).read_text()
        inst = cls(source)
        return inst

    def get_clause(self, kind):
        return get_clause(self.spec, kind)

    @property
    def roles(self):
        return self.get_clause("who")

    @property
    def parameters(self):
        return [p["name"] for pc in self.get_clause("what") for p in pc]

    @property
    def private(self):
        return (
            set(a.name for a in self.actions)
            .union(p for a in self.actions for p in a.parameters)
            .difference(self.parameters)
            .union(a.autonomy_parameter for a in self.actions)
            .union(self.alt_parameters.keys())
            .union(self.all_delegations)
        )

    @property
    def keys(self):
        for pc in self.get_clause("what"):
            for p in pc:
                if "key" in p and p["key"] != None:
                    yield p["name"]

    @property
    def conflicts(self):
        return self.get_clause("conflicts") or []

    @property
    def saysos(self):
        return self.get_clause("sayso")

    def priorities(self, parameter):
        for c in self.saysos:
            if parameter in c["parameters"]:
                return c["roles"]
        return []

    def can_bind(self, role, parameter):
        """Check if role can bind parameter in some message (ignoring priority)"""
        for c in self.saysos:
            if role in c["roles"]:
                if parameter in c["parameters"]:
                    return True

        # only the actor can bind an action's autonomy parametors
        for a in self.actions:
            if parameter == a.autonomy_parameter and a.actor == role:
                return True
            elif parameter == a.autonomy_parameter and a.actor != role:
                return False

        # anyone can bind parameters that aren't in a sayso clause
        return not any(parameter in c["parameters"] for c in self.saysos)

    def can_be_delegated(self, role, parameter):
        """
        Returns true if role can be delegated parameter;
        In other words, if role is in the priority list for parameter but not first
        """
        roles = self.priorities(parameter)
        if roles:
            return role in roles and roles.index(role) > 0

    def delegates_to(self, role, parameter):
        "Returns the next role in the priority list for parameter after role, if any"
        roles = self.priorities(parameter)
        if roles and role in roles:
            pos = roles.index(role)
            if pos + 1 < len(roles):
                return roles[pos + 1]

    def delegations(self, role, parameter):
        if self.can_be_delegated(role, parameter):
            yield f"{parameter}@{role}"
        to = self.delegates_to(role, parameter)
        if to:
            yield f"{parameter}@{to}"

    @property
    def all_delegations(self):
        ds = set()
        for r in self.roles:
            for a in self.actions:
                for p in a.parameters:
                    for d in self.delegations(r, p):
                        ds.add(d)
        return ds

    def can_see(self, role, action):
        """
        Return true if role can see action:
          Either role can perform action or is explicitly allowed to see it
        """
        if action.actor == role:
            return True
        for c in self.get_clause("see"):
            if role in c["roles"] and action.name in c["parameters"]:
                return True

    def observes(self, role, parameter):
        """
        Check if a role can observe a parameter or not.
        Roles should be able to observe all parameters from their own actions,
        plus any parameters declared in the 'sees' section."""

        # A parameter can be seen if the role has an action involving it
        for x in chain(self.get_clause("actions"), self.get_clause("see")):
            if (
                role in x.get("roles", []) or role == x.get("actor")
            ) and parameter in x["parameters"]:
                return True

    def observers(self, parameter):
        "A sequence of roles that can observe parameter"
        for r in self.roles:
            if self.observes(r, parameter):
                yield r

    def extend_schemas(self, action):
        # add nil parameters for conflicts
        conflicts = []
        for c in self.conflicts:
            if action.name in c:
                conflicts.extend(a for a in c if a != action.name)
        if conflicts:
            for s in action.schemas():
                yield reduce(lambda s, c: s + ((c, "nil"),), conflicts, s)
        else:
            yield from action.schemas()

    @property
    def alt_parameters(self):
        alts = {}
        i = 0
        for c in self.get_clause("what"):
            if len(c) > 1:
                for p in c:
                    alts[p["name"]] = f"done{i}"
                i += 1
        return alts

    def recipients(self, action):
        """
        The set of roles that can receive action
        Recipients are roles that can see the action, except the actor
        """
        recipients = set()
        for r in self.roles:
            if r != action.actor and self.can_see(r, action):
                # if the role can see the action, it can receive the message
                recipients.add(r)
        return recipients

    def messages(self, action, protocol=None):
        for s in self.extend_schemas(action):
            n = 0
            for r in self.recipients(action):
                parameters = []
                for p in s:
                    if p[0] == action.autonomy_parameter:
                        aps = []
                        if n == 0:
                            aps.append(Parameter(p[0], "out"))
                        else:
                            aps.append(Parameter(p[0], "in"))
                            aps.append(Parameter(p[0] + str(n + 1), "out"))
                        self.autonomy_parameters.update(aps)
                        parameters.extend(aps)
                    else:
                        parameters.append(
                            Parameter(p[0], p[1] if n == 0 or p[1] != "out" else "in")
                        )

                yield Message(
                    parent=protocol,
                    name=action.name,
                    sender=action.actor,
                    recipient=Role(r),
                    parameters=parameters,
                    validate=False,
                )
                n += 1

    def completion_messages(self, protocol=None):
        for p in self.alt_parameters:
            keys = set()
            for a in self.actions:
                if p in a.expanded_parameters:
                    for k in a.keys:
                        keys.add(k)
            for s in self.roles:
                if self.can_bind(s, p):
                    alt = self.alt_parameters[p]
                    recipients = self.observers(p)
                    for r in recipients:
                        if r != s:
                            yield Message(
                                name=f"{p}#{alt}",
                                parent=protocol,
                                sender=s,
                                recipient=r,
                                parameters=[Parameter(k, "in", "key") for k in keys]
                                + [Parameter(p, "in"), Parameter(alt, "out")],
                                validate=False,
                            )

    def to_bspl(self, name):
        p = Protocol(
            name,
            roles=self.roles,
            public_parameters=[
                Parameter(p, "out", key=p in self.keys)
                for p in self.parameters
                if p not in self.alt_parameters
            ]
            + [Parameter(p, "out") for p in set(self.alt_parameters.values())],
            private_parameters=chain(
                [Parameter(p, None) for p in self.private], self.autonomy_parameters
            ),
        )
        for r in chain(
            (m for a in self.actions for m in self.messages(a, p)),
            self.completion_messages(p),
        ):
            p.add_reference(r)
        return p
