# ui/bot_worker.py
from PySide6.QtCore import QObject, Signal

class BotWorker(QObject):
    finished = Signal(object, str, str)
    def __init__(self, bot_agent, board, label):
        super().__init__()
        self.bot_agent = bot_agent
        self.board = board.copy()
        self.label = label
    def run(self):
        move, reason = self.bot_agent.choose_move(self.board, debug=True)
        self.finished.emit(move, self.label, reason or "")
