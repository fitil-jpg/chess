from metrics import MetricsManager

# Тимчасовий test board — можна завантажити з FEN або вручну
test_board = [
    [None, None, None, None, 'black-king', None, None, None],
    [None, None, 'white-knight', N  one, None, None, None, None],
    [None]*8,
    [None]*8,
    [None]*8,
    [None]*8,
    [None, 'white-pawn', None, None, None, None, None, None],
    ['white-rook', None, None, None, 'white-king', None, None, None],
]

metrics = MetricsManager(test_board)
metrics.update_all_metrics()
print(metrics.get_metrics())
