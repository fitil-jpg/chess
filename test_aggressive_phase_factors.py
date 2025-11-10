#!/usr/bin/env python3
"""Тестування нових фазово-залежних коефіцієнтів AggressiveBot"""

import chess
from chess_ai.aggressive_bot import AggressiveBot
from core.evaluator import Evaluator
from utils import GameContext
from core.phase import GamePhaseDetector

def test_phase_factors():
    """Тестуємо різні коефіцієнти для фаз гри"""
    
    # Створюємо бота з кастомними коефіцієнтами
    custom_factors = {
        "opening": 1.2,
        "middlegame": 1.3, 
        "endgame": 1.1
    }
    
    bot = AggressiveBot(chess.WHITE, phase_factors=custom_factors)
    
    print("=== Тестування фазово-залежних коефіцієнтів ===")
    print(f"Коефіцієнти за замовчуванням: {bot.phase_factors}")
    
    # Тестова позиція - дебют
    opening_fen = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
    board = chess.Board(opening_fen)
    evaluator = Evaluator(board)
    
    # Симулюємо програш в матеріалі
    context = GameContext(material_diff=-2)  # програємо 2 пункти
    
    phase = GamePhaseDetector.detect(board)
    print(f"\nДебютна позиція: {phase}")
    print(f"FEN: {opening_fen}")
    
    move, confidence = bot.choose_move(board, context=context, evaluator=evaluator, debug=True)
    print(f"Обраний хід: {move}, впевненість: {confidence:.2f}")
    
    # Тестова позиція - міттєгра
    middlegame_fen = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 0 5"
    board.set_fen(middlegame_fen)
    evaluator = Evaluator(board)
    
    phase = GamePhaseDetector.detect(board)
    print(f"\nМіттєгра позиція: {phase}")
    print(f"FEN: {middlegame_fen}")
    
    move, confidence = bot.choose_move(board, context=context, evaluator=evaluator, debug=True)
    print(f"Обраний хід: {move}, впевненість: {confidence:.2f}")
    
    # Тестова позиція - ендшпіль
    endgame_fen = "8/8/8/5k2/8/8/4K3/8 w - - 0 1"
    board.set_fen(endgame_fen)
    evaluator = Evaluator(board)
    
    phase = GamePhaseDetector.detect(board)
    print(f"\nЕндшпільна позиція: {phase}")
    print(f"FEN: {endgame_fen}")
    
    move, confidence = bot.choose_move(board, context=context, evaluator=evaluator, debug=True)
    print(f"Обраний хід: {move}, впевненість: {confidence:.2f}")

def test_custom_factors():
    """Тестуємо кастомні коефіцієнти"""
    
    # Кастомні коефіцієнти
    my_factors = {
        "opening": 1.4,
        "middlegame": 1.6,
        "endgame": 1.3
    }
    
    bot = AggressiveBot(chess.WHITE, phase_factors=my_factors)
    
    print("\n=== Тестування кастомних коефіцієнтів ===")
    print(f"Мої коефіцієнти: {bot.phase_factors}")
    
    # Дебют з можливим взяттям
    fen = "rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
    board = chess.Board(fen)
    evaluator = Evaluator(board)
    context = GameContext(material_diff=-1)
    
    move, confidence = bot.choose_move(board, context=context, evaluator=evaluator, debug=True)
    print(f"Хід у дебюті: {move}, впевненість: {confidence:.2f}")

if __name__ == "__main__":
    test_phase_factors()
    test_custom_factors()
