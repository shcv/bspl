from importlib.util import find_spec
from .paths import handle_safety, handle_liveness, handle_paths, max_paths
from .mambo import match_paths
from ..generators.mambo import nonlive, unsafe
from ..parsers.bspl import load_protocols


HAS_SAT = find_spec("boolexpr") is not None

if HAS_SAT:
    from .sat import SATCommands


class Verify:
    def __init__(self):
        self.safety = handle_safety
        self.liveness = handle_liveness
        self.paths = handle_paths
        if HAS_SAT:
            self.sat = SATCommands()

    def deadwood(self, *files):
        """Find any messages which are never sent."""
        for protocol in load_protocols(files):
            print(f"{protocol.name} ({protocol.path}): ")
            deadwood = set(protocol.messages.values())
            for p in max_paths(protocol):
                deadwood = deadwood.difference(e.msg for e in p)
            print(deadwood)

    def unbound(self, *files):
        """Find any parameters which are never bound."""
        for protocol in load_protocols(files):
            print(f"{protocol.name} ({protocol.path}): ")
            unbound = set(p.name for p in protocol.parameters.values())
            for p in max_paths(protocol):
                unbound = unbound.difference(param for e in p for param in e.msg.outs)
            print(unbound)

    def unused(self, *files):
        """Find any parameters which are bound but never used ('in' in another message)."""
        for protocol in load_protocols(files):
            print(f"{protocol.name} ({protocol.path}): ")
            unused = set()
            for p in max_paths(protocol):
                for e in p:
                    unused.update(e.msg.outs)
            for p in max_paths(protocol):
                for e in p:
                    unused.difference_update(e.msg.ins)
                    unused.difference_update(e.msg.nils)
            print(unused)
