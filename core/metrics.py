class EvaluationTuner:
    def __init__(self):
        self.weights = {
            'center_control': 1.0,
            'piece_activity': 1.0,
            'king_safety': 1.0,
            'material_balance': 1.0,
        }

    def adjust_weights(self, phase):
        if phase == 'opening':
            self.weights['center_control'] = 1.5
            self.weights['king_safety'] = 0.8
        elif phase == 'endgame':
            self.weights['king_safety'] = 1.5
            self.weights['piece_activity'] = 1.2

    def evaluate_position(self, board_metrics):
        score = 0.0
        for metric, value in board_metrics.items():
            weight = self.weights.get(metric, 0.0)
            score += weight * value
        return score
    
class BoardMetrics:
    def __init__(self):
        self.metrics = {
            'material_balance': 0,
            'center_control': 0,
            'piece_activity': 0,
            'king_safety': 0,
        }

    def update_from_board(self, board, analyzer):
        self.metrics['material_balance'] = self._calculate_material(board)
        self.metrics['center_control'] = self._calculate_center_control(board)
        self.metrics['piece_activity'] = self._calculate_activity(board)
        self.metrics['king_safety'] = self._calculate_king_safety(board, analyzer)

    def _calculate_material(self, board):
        piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
        score = 0
        for piece in board.get_all_pieces():
            value = piece_values.get(piece.symbol.upper(), 0)
            score += value if piece.color == 'white' else -value
        return score

    def _calculate_center_control(self, board):
        center_squares = ['d4', 'd5', 'e4', 'e5']
        control = 0
        for sq in center_squares:
            attackers = board.get_attackers('white', sq)
            control += len(attackers)
            attackers = board.get_attackers('black', sq)
            control -= len(attackers)
        return control

    def _calculate_activity(self, board):
        active_squares = 0
        for piece in board.get_all_pieces():
            if piece.color == 'white':
                active_squares += len(piece.get_attacked_squares(board))
            else:
                active_squares -= len(piece.get_attacked_squares(board))
        return active_squares

    def _calculate_king_safety(self, board, analyzer):
        # Заглушка — в майбутньому врахувати наявність атак біля короля
        return 0

    def get_metrics(self):
        return self.metrics.copy()
    
    def _calculate_mobility(self, board):
        score = 0
        for piece in board.get_all_pieces():
            moves = piece.get_attacked_squares(board)
            if piece.color == 'white':
                score += len(moves)
            else:
                score -= len(moves)
        return score