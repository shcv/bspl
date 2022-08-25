from .message import Message
from bspl import protocol, load_file
import logging

logger = logging.getLogger("bspl")


def instantiate(adapter):
    def inner(schema, *args, **kwargs):
        payload = schema.construct(*args, **kwargs)
        return Message(schema, payload, adapter=adapter)

    return inner


def match(schema, **params):
    """Construnct instances of schema that match params"""
    h = schema.adapter.history
    contexts = h.matching_contexts(**params)
    candidates = set()
    for c in contexts:
        if (
            h.check_outs(schema, c)
            and all(p in c.bindings for p in schema.ins)
            and not any(p in c.bindings for p in schema.nils)
        ):
            candidates.add(
                schema(
                    **{p: c.bindings[p] for p in schema.parameters if p in c.bindings}
                )
            )
    return candidates
