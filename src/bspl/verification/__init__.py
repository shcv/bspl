from importlib.util import find_spec
from ttictoc import Timer
from .paths import handle_safety, handle_liveness, handle_paths, max_paths
from .mambo import match_paths
from ..generators.mambo import nonlive, unsafe
from ..parsers.bspl import load_protocols

HAS_SAT = find_spec("boolexpr") is not None

if HAS_SAT:
    from .sat import SATCommands


class MamboCommands:
    def liveness(self, *files):
        """Check liveness properties for each protocol in FILES"""
        for protocol in load_protocols(files):
            print(f"{protocol.name} ({protocol.path}):")
            t = Timer()
            t.start()
            q = nonlive(protocol)
            result = next(
                match_paths(protocol, q, residuate=True, incremental=True, prune=True),
                [],
            )
            elapsed = t.stop()
            if result:
                print({"elapsed": elapsed, "live": False, "path": result})
            else:
                print({"elapsed": elapsed, "live": True})

    def safety(self, *files):
        """Check safety properties for each protocol in FILES"""
        for protocol in load_protocols(files):
            print(f"{protocol.name} ({protocol.path}):")
            t = Timer()
            t.start()
            q = unsafe(protocol)
            if not q:
                print({"elapsed": t.stop(), "safe": True, "query": q})
                continue
            result = next(
                match_paths(protocol, q, residuate=True, incremental=True, prune=True),
                [],
            )
            elapsed = t.stop()
            if result:
                print({"elapsed": elapsed, "safe": False, "query": q, "path": result})
            else:
                print({"elapsed": elapsed, "safe": True, "query": q})

    def query(self, path, query):
        for protocol in load_protocols([path]):
            print(f"{protocol.name} ({protocol.path}):")
            paths = [
                str(p.events)
                for p in match_paths(
                    protocol, query, residuate=True, incremental=True, prune=True
                )
            ]
            if paths:
                print("\n".join(paths))
            else:
                print("No matching enactments")


class Verify:
    def __init__(self):
        self.safety = handle_safety
        self.liveness = handle_liveness
        self.paths = handle_paths
        self.mambo = MamboCommands()
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

    def solitary(self, *files):
        """Find any parameters which only appear once."""
        for protocol in load_protocols(files):
            print(f"{protocol.name} ({protocol.path}): ")
            uses = {p: set() for p in protocol.parameters}
            for p in uses:
                for m in protocol.messages.values():
                    if p in m.parameters:
                        uses[p].add(m)

            solo = set(p for p in uses if len(uses[p]) == 1)
            print(solo)
