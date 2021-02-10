from .history import Message
from protocheck import protocol
from protocheck.bspl import load_file
import logging

logger = logging.getLogger("bungie")


def instantiate(schema, *args, **kwargs):
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

    return Message(schema, payload)


protocol.Message.__call__ = instantiate
