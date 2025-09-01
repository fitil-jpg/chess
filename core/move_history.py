import logging
logger = logging.getLogger(__name__)

class MoveHistory:
    def __init__(self):
        self.history = []

    def record(self, move):
        self.history.append(move)

    def undo(self):
        if self.history:
            return self.history.pop()
        return None

    def get_last(self):
        if self.history:
            return self.history[-1]
        return None

    def get_all(self):
        return list(self.history)
