from .paths import handle_safety, handle_liveness, handle_all_paths


class Verify:
    def __init__(self):
        self.safety = handle_safety
        self.liveness = handle_liveness
        self.all_paths = handle_all_paths
