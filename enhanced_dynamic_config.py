"""
Enhanced DynamicBot configuration with stronger endgame focus.
Цей файл містить конфігурації для DynamicBot з підвищеними вагами EndgameBot
в залежності від фази гри та матеріалу на дошці.
"""

# Базова конфігурація з сильним акцентом на ендшпіль
ENHANCED_ENDGAME_WEIGHTS = {
    # Базові ваги
    "aggressive": 0.8,
    "fortify": 0.9,
    "critical": 1.0,
    "pawn": 0.7,
    "king": 1.1,  # Підвищена вага для короля
    "endgame": 1.0,  # Буде динамічно змінюватись
    "random": 0.0,
    "center": 0.8,
    "neural": 0.9,
    
    # Фазо-залежні ваги
    "opening": {
        "aggressive": 1.0,
        "fortify": 0.8,
        "critical": 0.9,
        "pawn": 0.6,
        "king": 0.7,
        "endgame": 0.3,  # Мінімальний вплив в дебюті
        "center": 1.2,
        "neural": 0.8,
    },
    
    "middlegame": {
        "aggressive": 1.1,
        "fortify": 0.9,
        "critical": 1.0,
        "pawn": 0.8,
        "king": 0.9,
        "endgame": 0.7,  # Помірний вплив в міттельшпілі
        "center": 1.0,
        "neural": 1.0,
    },
    
    "endgame": {
        "aggressive": 0.6,  # Агресивність менш важлива
        "fortify": 0.8,
        "critical": 0.9,
        "pawn": 1.2,  # Пішаки критично важливі
        "king": 1.3,  # Король - головна фігура
        "endgame": 2.0,  # Максимальний пріоритет в ендшпілі
        "center": 0.7,
        "neural": 0.8,
    }
}

# Конфігурація з адаптивними вагами залежно від матеріалу
MATERIAL_ADAPTIVE_WEIGHTS = {
    "base": ENHANCED_ENDGAME_WEIGHTS,
    
    # Правила адаптації ваг залежно від кількості матеріалу
    "material_thresholds": {
        "heavy_endgame": 15,  # <= 15 очок матеріалу - сильний ендшпіль
        "medium_endgame": 23,  # <= 23 очки - середній ендшпіль
        "late_endgame": 10,   # <= 10 очок - пізній ендшпіль
    },
    
    "adaptive_multipliers": {
        "heavy_endgame": {
            "endgame": 1.8,
            "king": 1.4,
            "pawn": 1.3,
            "aggressive": 0.5,
        },
        "medium_endgame": {
            "endgame": 1.5,
            "king": 1.2,
            "pawn": 1.1,
            "aggressive": 0.7,
        },
        "late_endgame": {
            "endgame": 2.5,  # Максимальний пріоритет
            "king": 1.6,
            "pawn": 1.4,
            "aggressive": 0.3,
        }
    }
}

# Конфігурація для турнірної гри
TOURNAMENT_ENDGAME_CONFIG = {
    "weights": MATERIAL_ADAPTIVE_WEIGHTS["base"],
    
    # Додаткові параметри для кращої гри в ендшпілі
    "phase_weights": MATERIAL_ADAPTIVE_WEIGHTS["base"],
    
    # Підвищена різноманітність для знаходження нестандартних рішень
    "enable_diversity": True,
    "diversity_bonus": 0.35,
    
    # Контекстуальний бандит для адаптації до типу позицій
    "enable_bandit": True,
    "bandit_alpha": 0.2,
}

def create_endgame_focused_dynamic_bot(color: bool, material_count: int = None):
    """
    Створює DynamicBot з оптимізованими вагами для ендшпілю.
    
    Parameters
    ----------
    color : bool
        Колір бота (True для білих, False для чорних)
    material_count : int, optional
        Кількість матеріалу на дошці для адаптації ваг
        
    Returns
    -------
    DynamicBot
        Налаштований екземпляр DynamicBot
    """
    from chess_ai.dynamic_bot import DynamicBot
    
    # Визначаємо конфігурацію залежно від кількості матеріалу
    if material_count is not None:
        config = MATERIAL_ADAPTIVE_WEIGHTS.copy()
        
        # Вибираємо множники на основі матеріалу
        if material_count <= config["material_thresholds"]["late_endgame"]:
            multipliers = config["adaptive_multipliers"]["late_endgame"]
        elif material_count <= config["material_thresholds"]["heavy_endgame"]:
            multipliers = config["adaptive_multipliers"]["heavy_endgame"]
        elif material_count <= config["material_thresholds"]["medium_endgame"]:
            multipliers = config["adaptive_multipliers"]["medium_endgame"]
        else:
            multipliers = {}
        
        # Застосовуємо множники до базових ваг
        weights = config["base"].copy()
        for agent, multiplier in multipliers.items():
            if agent in weights:
                weights[agent] *= multiplier
    else:
        weights = TOURNAMENT_ENDGAME_CONFIG["weights"]
    
    # Створюємо бота з налаштованими вагами
    bot = DynamicBot(
        color=color,
        weights=weights,
        phase_weights=TOURNAMENT_ENDGAME_CONFIG["phase_weights"],
        enable_diversity=TOURNAMENT_ENDGAME_CONFIG["enable_diversity"],
        diversity_bonus=TOURNAMENT_ENDGAME_CONFIG["diversity_bonus"],
        enable_bandit=TOURNAMENT_ENDGAME_CONFIG["enable_bandit"],
        bandit_alpha=TOURNAMENT_ENDGAME_CONFIG["bandit_alpha"],
    )
    
    return bot

def get_material_count(board: chess.Board) -> int:
    """
    Розраховує загальну кількість матеріалу на дошці.
    
    Parameters
    ----------
    board : chess.Board
        Шахова дошка
        
    Returns
    -------
    int
        Загальна вартість матеріалу в пішаках
    """
    piece_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0
    }
    
    total = 0
    for piece_type in piece_values:
        total += len(board.pieces(piece_type, chess.WHITE)) * piece_values[piece_type]
        total += len(board.pieces(piece_type, chess.BLACK)) * piece_values[piece_type]
    
    return total

# Приклад використання
if __name__ == "__main__":
    import chess
    
    # Створюємо тестову дошку
    board = chess.Board()
    
    # Отримуємо кількість матеріалу
    material = get_material_count(board)
    print(f"Material count: {material}")
    
    # Створюємо бота з адаптивними вагами
    bot = create_endgame_focused_dynamic_bot(chess.WHITE, material)
    print("Enhanced DynamicBot created with endgame-focused weights")
