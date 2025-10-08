import chess
import types

from chess_ai.dynamic_bot import DynamicBot


def _set_agent_choices(bot: DynamicBot, mapping):
    """Replace each agent's choose_move with a deterministic one.

    mapping: {agent_name: (uci_move or None, confidence)}
    """
    for i, (agent, name) in enumerate(bot.agents):
        uci, conf = mapping.get(name, (None, 0.0))
        def make_choice(u, c):
            def chooser(self, board, context=None, evaluator=None, debug=False):
                if u is None:
                    return None, 0.0
                try:
                    mv = chess.Move.from_uci(u)
                except Exception:
                    return None, 0.0
                if mv not in board.legal_moves:
                    return None, 0.0
                return mv, float(c)
            return chooser
        agent.choose_move = types.MethodType(make_choice(uci, conf), agent)


def test_phase_aware_weights_opening_selection():
    board = chess.Board()  # opening
    # Opening: prefer aggressive over fortify via phase weights
    phase_weights = {
        "opening": {"aggressive": 2.0, "fortify": 0.5},
        "middlegame": {},
        "endgame": {},
    }
    bot = DynamicBot(color=chess.WHITE, phase_weights=phase_weights, enable_diversity=False, enable_bandit=False)

    # Aggressive -> e2e4 with conf 1.0; Fortify -> d2d4 with conf 1.0
    # Others return None
    _set_agent_choices(
        bot,
        {
            "aggressive": ("e2e4", 1.0),
            "fortify": ("d2d4", 1.0),
            "critical": (None, 0.0),
            "endgame": (None, 0.0),
            "center": (None, 0.0),
            "neural": (None, 0.0),
            "random": (None, 0.0),
            "r": (None, 0.0),
        },
    )

    move, score = bot.choose_move(board, debug=True)
    assert move == chess.Move.from_uci("e2e4")
    assert score > 0.0


def test_diversity_bonus_can_flip_choice():
    board = chess.Board()
    bot = DynamicBot(color=chess.WHITE, enable_diversity=True, diversity_bonus=0.5, enable_bandit=False)

    # Two distinct, non-overlapping ideas from agents A and F; base conf 1.0
    # Center proposes a slightly higher base conf 1.1 — would win without diversity
    _set_agent_choices(
        bot,
        {
            "aggressive": ("e2e4", 1.0),
            "fortify": ("d2d4", 1.0),
            "center": ("g1f3", 1.1),
            "critical": (None, 0.0),
            "endgame": (None, 0.0),
            "neural": (None, 0.0),
            "random": (None, 0.0),
        },
    )

    move, _ = bot.choose_move(board, debug=True)
    # With diversity bonus, one of e2e4/d2d4 should surpass g1f3
    assert move in {chess.Move.from_uci("e2e4"), chess.Move.from_uci("d2d4")}


def test_bandit_updates_multiplier_for_supporting_agent(monkeypatch):
    board = chess.Board()
    # Enable bandit; keep diversity off to isolate
    bot = DynamicBot(color=chess.WHITE, enable_bandit=True, bandit_alpha=0.5, enable_diversity=False)

    # Favor aggressive slightly so it is chosen deterministically
    phase_weights = {
        "opening": {"aggressive": 1.1, "center": 1.0},
    }
    bot.weights_by_phase.update(phase_weights)

    _set_agent_choices(
        bot,
        {
            "aggressive": ("e2e4", 1.0),
            "center": ("d2d4", 1.0),
            "critical": (None, 0.0),
            "fortify": (None, 0.0),
            "endgame": (None, 0.0),
            "neural": (None, 0.0),
            "random": (None, 0.0),
        },
    )

    # Patch Evaluator.position_score to yield a positive delta only for e2e4
    from core import evaluator as core_eval

    orig_position_score = core_eval.Evaluator.position_score

    def fake_position_score(self, board_arg=None, color=None):
        b = board_arg or self.board
        if len(b.move_stack) > 0 and b.peek().uci() == "e2e4":
            return 300  # positive improvement
        return 0

    monkeypatch.setattr(core_eval.Evaluator, "position_score", fake_position_score, raising=True)

    try:
        # Snapshot multiplier before
        from core.phase import GamePhaseDetector
        bucket = f"{GamePhaseDetector.detect(board)}|quiet|norm"
        before = bot._bandit_weights[bucket]["aggressive"]

        mv, _ = bot.choose_move(board, debug=True)
        assert mv == chess.Move.from_uci("e2e4")

        after = bot._bandit_weights[bucket]["aggressive"]
        assert after > before
    finally:
        # Restore to avoid leaking monkeypatch in case of failure paths without fixture teardown
        monkeypatch.setattr(core_eval.Evaluator, "position_score", orig_position_score, raising=True)

