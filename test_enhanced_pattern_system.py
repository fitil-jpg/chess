#!/usr/bin/env python3
"""
Тест улучшенной системы паттернов
=================================

Скрипт для тестирования новой системы паттернов и EnhancedDynamicBot.
"""

import sys
import chess
import json
from pathlib import Path

# Добавить путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from chess_ai.enhanced_pattern_system import (
    PatternManager, ChessPatternEnhanced, PatternCategory,
    ExchangeType, PatternPiece, ExchangeSequence, create_default_patterns
)
from chess_ai.enhanced_pattern_detector import EnhancedPatternDetector
from chess_ai.enhanced_dynamic_bot import EnhancedDynamicBot
from chess_ai.stockfish_bot import StockfishBot
import logging

# Настроить логирование
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_pattern_system():
    """Тестировать систему паттернов"""
    print("🎯 Тестирование системы паттернов...")
    
    # Создать менеджер паттернов
    manager = PatternManager()
    
    # Создать паттерны по умолчанию
    default_patterns = create_default_patterns()
    for pattern in default_patterns:
        success = manager.create_pattern(pattern)
        print(f"  Создан паттерн: {pattern.name} - {'✅' if success else '❌'}")
    
    # Показать статистику
    stats = manager.get_pattern_statistics()
    print(f"\n📊 Статистика паттернов:")
    print(f"  Всего паттернов: {stats['total_patterns']}")
    print(f"  Включено: {stats['enabled_patterns']}")
    print(f"  По категориям: {stats['by_category']}")
    
    return manager


def test_pattern_detection():
    """Тестировать обнаружение паттернов"""
    print("\n🔍 Тестирование обнаружения паттернов...")
    
    # Создать детектор
    detector = EnhancedPatternDetector()
    
    # Тестовые позиции
    test_positions = [
        # Начальная позиция
        ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "Начальная позиция"),
        
        # Позиция с тактикой
        ("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 4", "Итальянская партия"),
        
        # Эндшпиль
        ("8/8/8/3k4/8/3K4/3R4/8 w - - 0 1", "Ладейный эндшпиль"),
        
        # Тактическая позиция
        ("r3k2r/ppp2ppp/2n1bn2/2bpp3/2B1P3/3P1N2/PPP2PPP/RNBQ1RK1 w kq - 0 8", "Тактическая позиция"),
    ]
    
    for fen, description in test_positions:
        print(f"\n  📋 {description}:")
        board = chess.Board(fen)
        
        matches = detector.detect_patterns_in_position(board, max_patterns=3)
        
        if matches:
            for i, match in enumerate(matches, 1):
                print(f"    {i}. {match.pattern.name} (уверенность: {match.confidence:.2f})")
                print(f"       Категория: {match.pattern.category.value}")
                if match.suggested_move:
                    print(f"       Предлагаемый ход: {match.suggested_move}")
                print(f"       Объяснение: {match.explanation}")
        else:
            print("    Паттерны не обнаружены")


def test_enhanced_dynamic_bot():
    """Тестировать улучшенный DynamicBot"""
    print("\n🤖 Тестирование EnhancedDynamicBot...")
    
    # Создать ботов
    enhanced_bot = EnhancedDynamicBot(chess.BLACK, anti_stockfish_mode=True)
    
    # Тестовая позиция
    board = chess.Board("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")
    
    print(f"  Позиция: {board.fen()}")
    
    # Получить ход от бота
    move, confidence = enhanced_bot.choose_move(board, debug=True)
    
    if move:
        print(f"  Выбранный ход: {move} (уверенность: {confidence:.3f})")
        print(f"  Причина: {enhanced_bot.get_last_reason()}")
        print(f"  Характеристики: {enhanced_bot.get_last_features()}")
    else:
        print("  ❌ Ход не выбран")


def test_bot_vs_bot():
    """Тестировать игру бот против бота"""
    print("\n⚔️  Тестирование игры EnhancedDynamicBot vs обычный DynamicBot...")
    
    try:
        from chess_ai.dynamic_bot import DynamicBot
        
        # Создать ботов
        enhanced_bot = EnhancedDynamicBot(chess.WHITE, anti_stockfish_mode=False)
        regular_bot = DynamicBot(chess.BLACK)
        
        # Сыграть несколько ходов
        board = chess.Board()
        moves_played = 0
        max_moves = 10
        
        print(f"  Начальная позиция: {board.fen()}")
        
        while not board.is_game_over() and moves_played < max_moves:
            if board.turn == chess.WHITE:
                # Ход Enhanced бота
                move, confidence = enhanced_bot.choose_move(board, debug=False)
                bot_name = "Enhanced"
            else:
                # Ход обычного бота
                move, confidence = regular_bot.choose_move(board, debug=False)
                bot_name = "Regular"
            
            if move:
                san = board.san(move)
                board.push(move)
                moves_played += 1
                print(f"    {moves_played}. {bot_name}: {san} (уверенность: {confidence:.3f})")
            else:
                print(f"    ❌ {bot_name} не смог выбрать ход")
                break
        
        print(f"  Финальная позиция: {board.fen()}")
        
        if board.is_game_over():
            result = board.result()
            print(f"  🏁 Результат: {result}")
        
    except ImportError as e:
        print(f"  ⚠️  Не удалось импортировать DynamicBot: {e}")


def test_json_storage():
    """Тестировать JSON хранение паттернов"""
    print("\n💾 Тестирование JSON хранения...")
    
    manager = PatternManager("patterns/test")
    
    # Создать тестовый паттерн
    test_pattern = ChessPatternEnhanced(
        id="test_pattern_001",
        name="Тестовый паттерн",
        description="Паттерн для тестирования JSON сериализации",
        category=PatternCategory.TACTICAL,
        fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        key_move="e2e4",
        participating_pieces=[
            PatternPiece("e2", "pawn", "white", "attacker", 1.0),
            PatternPiece("e4", "pawn", "white", "target", 0.8)
        ],
        exchange_sequence=ExchangeSequence(
            moves=["e2e4"],
            material_balance=0,
            positional_gain=10.0,
            evaluation_change=10.0,
            probability=0.9
        ),
        exchange_type=ExchangeType.EQUAL_TRADE,
        frequency=0.8,
        success_rate=0.7,
        tags=["test", "opening", "center"]
    )
    
    # Сохранить паттерн
    success = manager.create_pattern(test_pattern)
    print(f"  Создание паттерна: {'✅' if success else '❌'}")
    
    # Загрузить паттерн
    loaded_pattern = manager.load_pattern("test_pattern_001")
    if loaded_pattern:
        print(f"  Загрузка паттерна: ✅")
        print(f"    Название: {loaded_pattern.name}")
        print(f"    Категория: {loaded_pattern.category.value}")
        print(f"    Фигур в паттерне: {len(loaded_pattern.participating_pieces)}")
        print(f"    Есть размен: {loaded_pattern.exchange_sequence is not None}")
    else:
        print(f"  Загрузка паттерна: ❌")
    
    # Показать все паттерны
    all_patterns = manager.get_patterns()
    print(f"  Всего паттернов в менеджере: {len(all_patterns)}")


def main():
    """Главная функция тестирования"""
    print("🚀 Запуск тестов улучшенной системы паттернов\n")
    
    try:
        # Тест 1: Система паттернов
        manager = test_pattern_system()
        
        # Тест 2: Обнаружение паттернов
        test_pattern_detection()
        
        # Тест 3: EnhancedDynamicBot
        test_enhanced_dynamic_bot()
        
        # Тест 4: Игра бот против бота
        test_bot_vs_bot()
        
        # Тест 5: JSON хранение
        test_json_storage()
        
        print("\n✅ Все тесты завершены!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()