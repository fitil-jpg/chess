## 🧪 Простий тест для `BoardMetrics`

def test_board_metrics():
    board = Board()
    board.place_piece(Pawn('white', 'e2'))
    board.place_piece(Knight('white', 'g1'))
    board.place_piece(Pawn('black', 'e7'))

    analyzer = BoardAnalyzer(board)
    metrics = BoardMetrics()
    metrics.update_from_board(board, analyzer)

    result = metrics.get_metrics()
    print("Оцінка метрик:", result)
    assert isinstance(result, dict)
    assert 'material_balance' in result
