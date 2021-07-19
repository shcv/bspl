from .store import Message
from protocheck import protocol
from protocheck.bspl import load_file
import logging

logger = logging.getLogger("bungie")


def instantiate(adapter):
    def inner(schema, *args, **kwargs):
        payload = {}
        for i, p in enumerate(schema.parameters.values()):
            if i < len(args):
                payload[p] = args[i]

        for k in kwargs:
            if k in schema.parameters:
                payload[k] = kwargs[k]
            # else:
            #     logger.error(f'Parameter not in schema: {k}')
            #     return None

        return Message(schema, payload, adapter=adapter)

    return inner


def match(schema, **params):
    """Construnct instances of schema that match params"""
    h = schema.adapter.history
    contexts = h.matching_contexts(**params)
    candidates = set()
    for c in contexts:
        if h.check_outs(schema, c) and all(p in c.bindings for p in schema.ins):
            candidates.add(schema(**c.bindings))
    return candidates
