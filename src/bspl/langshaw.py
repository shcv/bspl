#!/usr/bin/env python3

from itertools import chain, product
from functools import reduce, partial
from .protocol import Protocol, Role, Parameter, Message
import re


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
    ds = {p[0]: delegates(p[0]) for p in s if delegates(p[0])}
    for d in ds:
        if getp(d, s)[1] == "out" and getp(ds[d], s)[1] != "nil":
            return
    return s


@some
def ensure_sayso(s):
    for p in s:
        if (
            not delegates(p[0])
            and p[1] == "nil"
            and all(d[1] == "nil" for d in s if delegates(d[0]) == p[0])
        ):
            return
    return s


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
            # if p in self.keys:
            #     yield map(lambda p: p + ("key",), product([p], self.possibilities(p)))
            # else:
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
                    ensure_sayso,
                    out_keys(self.keys),
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
        validate(spec)
        self.spec = spec
        self.actions = [Action(a, self) for a in self.get_clause("actions")]
        self.autonomy_parameters = set()

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
                if "key" in p:
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

    def can_see(self, role, parameter):
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
        for r in self.roles:
            if self.can_see(r, parameter):
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

    def recipients(self, action, schema):
        """
        The set of roles that can receive action
        Recipients are roles that can see the action, except the actor
        """
        recipients = set()
        for r in self.roles:
            if r != action.actor:
                for p in schema:
                    if p[1] == "out" and (
                        delegates_to(p[0]) == r or self.can_see(r, p[0])
                    ):
                        recipients.add(r)
        return recipients

    def messages(self, action, protocol=None):
        for s in self.extend_schemas(action):
            n = 0
            for r in self.recipients(action, s):
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
        print(p.parameters)
        for r in chain(
            (m for a in self.actions for m in self.messages(a, p)),
            self.completion_messages(p),
        ):
            p.add_reference(r)
        return p
