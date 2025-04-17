class Piece:
    def __init__(self, color, position, value=0):
        self.color = color
        self.position = position
        self.value = value

    def move(self, new_position):
        self.position = new_position

    def get_attacked_squares(self, board):
        return []

    def evaluate_position(self, board):
        return self.value

class Pawn(Piece):
    def __init__(self, color, position):
        super().__init__(color, position, value=1)

    def get_attacked_squares(self, board):
        return [...]  # логіка для пішака

class Knight(Piece):
    def __init__(self, color, position):
        super().__init__(color, position, value=3)

    def get_attacked_squares(self, board):
        return [...]  # логіка для коня

class Piece:
    def __init__(self, color, position):
        self.color = color
        self.position = position

    def move(self, new_position):
        self.position = new_position

    def get_attacked_squares(self, board):
        return []

    def evaluate_position(self, board):
        # Повертає статичну вартість фігури як приклад
        values = {
            'pawn': 1,
            'knight': 3,
            'bishop': 3,
            'rook': 5,
            'queen': 9,
            'king': 0
        }
        return values.get(self.__class__.__name__.lower(), 0)