from .paths import handle_safety, handle_liveness, handle_all_paths
from .sat import SATCommands


class Verify:
    def __init__(self):
        self.safety = handle_safety
        self.liveness = handle_liveness
        self.all_paths = handle_all_paths
        self.sat = SATCommands()
