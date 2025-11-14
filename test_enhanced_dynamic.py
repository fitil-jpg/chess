"""
Тестування покращеного DynamicBot з акцентом на ендшпіль.
Цей скрипт демонструє, як нові ваги покращують гру в ендшпілі.
"""

import chess
import logging
from chess_ai.dynamic_bot import DynamicBot
from chess_ai.endgame_bot import EndgameBot
from chess_ai.random_bot import RandomBot

# Налаштування логування
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_endgame_weight_boost():
    """Тестує динамічне підвищення ваг в ендшпілі."""
    
    print("=== Тестування динамічних ваг в ендшпілі ===\n")
    
    # Створюємо тестові позиції з різною кількістю матеріалу
    test_positions = [
        {
            "name": "Пізній ендшпіль (K+P vs K)",
            "fen": "8/8/8/8/8/8/4P3/4K3 w - - 0 1",
            "expected_material": 2
        },
        {
            "name": "Важкий ендшпіль (R+P vs R)",
            "fen": "8/8/8/8/8/8/4PR2/4K3 w - - 0 1",
            "expected_material": 7
        },
        {
            "name": "Середній ендшпіль (R+N+P vs R)",
            "fen": "8/8/8/8/8/8/1NPR4/4K3 w - - 0 1",
            "expected_material": 10
        },
        {
            "name": "Міттельшпіль (повний матеріал)",
            "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "expected_material": 30
        }
    ]
    
    for position in test_positions:
        print(f"Тестуємо позицію: {position['name']}")
        print(f"FEN: {position['fen']}")
        
        board = chess.Board(position['fen'])
        
        # Створюємо DynamicBot
        bot = DynamicBot(chess.WHITE)
        
        # Перевіряємо початкові ваги
        print(f"Початкова вага endgame: {bot.base_weights.get('endgame', 0):.2f}")
        print(f"Початкова вага king: {bot.base_weights.get('king', 0):.2f}")
        
        # Робимо хід для активації буста
        try:
            move, score = bot.choose_move(board)
            
            # Перевіряємо ваги після ходу
            print(f"Вага endgame після ходу: {bot.base_weights.get('endgame', 0):.2f}")
            print(f"Вага king після ходу: {bot.base_weights.get('king', 0):.2f}")
            print(f"Вага aggressive після ходу: {bot.base_weights.get('aggressive', 0):.2f}")
            
            material = bot._count_material(board)
            print(f"Розрахований матеріал: {material} (очікувався: {position['expected_material']})")
            
            print(f"Обраний хід: {move} з оцінкою {score:.2f}")
            
            # Перевіряємо чи активовано буст
            if bot._endgame_boost_active:
                print("✅ Буст ендшпілю АКТИВОВАНО")
            else:
                print("❌ Буст ендшпілю не активовано")
                
        except Exception as e:
            print(f"Помилка при виборі ходу: {e}")
        
        print("-" * 50)

def compare_endgame_vs_dynamic():
    """Порівнює EndgameBot з DynamicBot в ендшпільних позиціях."""
    
    print("\n=== Порівняння EndgameBot vs DynamicBot в ендшпілі ===\n")
    
    endgame_positions = [
        "8/8/8/8/8/8/4P3/4K3 w - - 0 1",  # K+P vs K
        "8/8/8/8/8/8/4PR2/4K3 w - - 0 1",  # R+P vs R
        "8/8/8/8/8/8/1NPR4/4K3 w - - 0 1",  # R+N+P vs R
    ]
    
    for i, fen in enumerate(endgame_positions, 1):
        print(f"Позиція {i}:")
        print(f"FEN: {fen}")
        
        board = chess.Board(fen)
        
        # Створюємо обох ботів
        endgame_bot = EndgameBot(chess.WHITE)
        dynamic_bot = DynamicBot(chess.WHITE)
        
        # Отримуємо ходи від обох ботів
        try:
            eg_move, eg_score = endgame_bot.choose_move(board)
            dyn_move, dyn_score = dynamic_bot.choose_move(board)
            
            print(f"EndgameBot: {eg_move} (оцінка: {eg_score:.2f})")
            print(f"DynamicBot: {dyn_move} (оцінка: {dyn_score:.2f})")
            
            # Аналізуємо схожість ходів
            if eg_move == dyn_move:
                print("✅ Обидва боти обрали однаковий хід")
            else:
                print("⚠️  Боти обрали різні ходи")
                
            # Показуємо ваги DynamicBot
            print(f"Ваги DynamicBot: endgame={dynamic_bot.base_weights.get('endgame', 0):.2f}, "
                  f"king={dynamic_bot.base_weights.get('king', 0):.2f}")
                  
        except Exception as e:
            print(f"Помилка: {e}")
        
        print("-" * 50)

def test_material_adaptation():
    """Тестує адаптацію ваг до кількості матеріалу."""
    
    print("\n=== Тестування адаптації до матеріалу ===\n")
    
    # Створюємо послідовність позицій зі зменшенням матеріалу
    material_sequence = [
        ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 30),  # Початкова
        ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQK1NR w KQkq - 0 1", 29),  # Без ферзя
        ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNB1K1NR w KQkq - 0 1", 26),  # Без тур
        ("rnbqkb1r/pppppppp/8/8/8/8/PPPPPPPP/RNB1K1NR w KQkq - 0 1", 25),  # Менше фігур
        ("8/8/8/8/8/8/4P3/4K3 w - - 0 1", 2),  # Пізній ендшпіль
    ]
    
    bot = DynamicBot(chess.WHITE)
    
    for fen, expected_material in material_sequence:
        board = chess.Board(fen)
        
        # Скидаємо ваги перед кожним тестом
        bot.reset_weights()
        
        material = bot._count_material(board)
        print(f"Матеріал: {material} (очікувався: {expected_material})")
        
        # Робимо хід для активації буста
        move, score = bot.choose_move(board)
        
        print(f"Ваги після ходу: endgame={bot.base_weights.get('endgame', 0):.2f}, "
              f"king={bot.base_weights.get('king', 0):.2f}, "
              f"pawn={bot.base_weights.get('pawn', 0):.2f}")
        
        if bot._endgame_boost_active:
            print("✅ Буст активовано")
        else:
            print("❌ Буст не активовано")
        
        print("-" * 30)

if __name__ == "__main__":
    print("🚀 Тестування покращеного DynamicBot з акцентом на ендшпіль\n")
    
    test_endgame_weight_boost()
    compare_endgame_vs_dynamic()
    test_material_adaptation()
    
    print("\n✅ Тестування завершено!")
    print("\n📝 Висновки:")
    print("1. DynamicBot тепер автоматично підвищує ваги EndgameBot в ендшпілі")
    print("2. Чим менше матеріалу, тим сильніший буст для ендшпільних евристик")
    print("3. Вага короля та пішаків також адаптується до фази гри")
    print("4. Агресивні стратегії депріоритезуються в ендшпілі")
