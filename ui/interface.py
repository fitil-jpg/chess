def print_debug_view(board, score, metrics, move='-', phase='-'):
    print("╔" + "═" * 46 + "╗")
    print(f"║  Move: {move:<6} Score: {score:<6} Phase: {phase:<6}         ║")
    print("╠" + "═" * 46 + "╣")
    print("║  a8 b8 c8 d8 e8 f8 g8 h8                     ║")
    for row in range(8, 0, -1):
        line = f"║  " + "  ".join("." for _ in range(8)) + f"                      {row}║"
        print(line)
    print("║  a1 b1 c1 d1 e1 f1 g1 h1                     ║")
    print("╟" + "─" * 46 + "╢")
    print("║  METRICS                                     ║")
    print("║  ─────────────                               ║")
    for k, v in metrics.items():
        print(f"║  {k.title():<17}: {v:<4}                      ║")
    print("╚" + "═" * 46 + "╝")
