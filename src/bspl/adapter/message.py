#!/usr/bin/env python3

import agentspeak
from agentspeak import Literal, Var
import re
from fastcore.foundation import camel2snake


def get_key(schema, payload):
    # schema.keys should be ordered, or sorted for consistency
    return ",".join(k + ":" + str(payload[k]) for k in schema.keys)


class Message:
    schema = None
    payload = {}
    acknowledged = False
    dest = None
    adapter = None
    meta = {}
    key = None

    def __init__(self, schema, payload, acknowledged=False, dest=None, adapter=None):
        self.schema = schema
        self.payload = payload
        self.acknowledged = acknowledged
        self.dest = dest
        self.adapter = adapter
        self.meta = {}

    @property
    def key(self):
        return get_key(self.schema, self.payload)

    def __repr__(self):
        payload = ",".join("{0}={1!r}".format(k, v) for k, v in self.payload.items())
        return f"{self.schema.name}({payload})"

    def __eq__(self, other):
        return self.payload == other.payload and self.schema == other.schema

    def __hash__(self):
        return hash(self.schema.qualified_name + self.key)

    def __getitem__(self, name):
        return self.payload[name]

    def __setitem__(self, name, value):
        if name not in self.schema.parameters:
            raise Exception(f"Parameter {name} is not in schema {self.schema}")
        adornment = self.schema.parameters[name].adornment
        if adornment == "out":
            self.payload[name] = value
            return value
        else:
            raise Exception(f"Parameter {name} is {adornment}, not out")

    def bind(self, **kwargs):
        for k, v in kwargs.items():
            self[k] = v
        return self

    def instance(self, **kwargs):
        """
        Return new instance of message, binding new parameters from kwargs
        """
        return self.schema(**self.payload).bind(**kwargs)

    def keys_match(self, other):
        return all(
            self.payload[k] == other.payload[k]
            for k in self.schema.keys
            if k in other.schema.parameters
        )

    def keys(self):
        return self.payload.keys()

    def project_key(self, schema):
        """Give the subset of this instance's keys that match the provided schema, in the order of the provided schema"""
        key = {}
        # use ordering from other schema
        for k in schema.keys:
            if k in self.schema.keys:
                key[k] = self[k]
        return key

    def send(self):
        self.adapter.send(self)

    def term(self):
        functor = self.schema.name
        parameters = self.schema.order_params(self.payload, default=agentspeak.Var)
        return Literal(
            functor, (self.schema.sender.name, self.schema.recipient.name, *parameters)
        )

    def enabled_term(self):
        parameters = self.schema.order_params(self.payload, default=None)
        msg = Literal(
            self.schema.name,
            (self.schema.sender.name, self.schema.recipient.name, *parameters),
        )
        return Literal("enabled", (msg,))

    def resolve(self, term, scope, memo={}):
        sender = term.args[0]
        recipient = term.args[1]
        payload = self.schema.zip_params(*term.args[2:])
        for p, v in payload.items():
            if isinstance(v, agentspeak.Var):
                val = agentspeak.deref(memo.get(v, v), scope)
                if (
                    isinstance(val, agentspeak.Var)
                    and self.schema.parameters[p].adornment == "out"
                ):
                    return False
                payload[p] = val
        return Message(self.schema, payload)
