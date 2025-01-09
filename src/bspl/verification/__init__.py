from importlib.util import find_spec
from .paths import handle_safety, handle_liveness, handle_all_paths

HAS_SAT = find_spec("boolexpr") is not None

if HAS_SAT:
    from .sat import SATCommands


class Verify:
    def __init__(self):
        self.safety = handle_safety
        self.liveness = handle_liveness
        self.all_paths = handle_all_paths
        if HAS_SAT:
            self.sat = SATCommands()
