"""
Enhanced Pattern System for Chess AI
====================================

Улучшенная система паттернов с поддержкой:
1. Управления паттернами (выбор и добавление пользовательских)
2. Фильтрации фигур, не участвующих в паттерне
3. Паттернов размена с предвидением 2-3 ходов
4. JSON хранения паттернов как отдельные файлы
"""

from __future__ import annotations
import json
import chess
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PatternCategory(Enum):
    """Категории паттернов"""
    TACTICAL = "tactical"           # Тактические приёмы
    OPENING = "opening"            # Дебютные паттерны
    ENDGAME = "endgame"           # Эндшпильные паттерны
    EXCHANGE = "exchange"          # Паттерны размена
    POSITIONAL = "positional"     # Позиционные паттерны
    DEFENSIVE = "defensive"       # Защитные паттерны
    ATTACK = "attack"             # Атакующие паттерны
    TRAP = "trap"                 # Ловушки


class ExchangeType(Enum):
    """Типы размена"""
    EQUAL_TRADE = "equal_trade"           # Равный размен
    FAVORABLE_TRADE = "favorable_trade"   # Выгодный размен
    SACRIFICE = "sacrifice"               # Жертва
    SIMPLIFICATION = "simplification"    # Упрощение позиции


@dataclass
class PatternPiece:
    """Фигура, участвующая в паттерне"""
    square: str                    # Поле (например, "e4")
    piece_type: str               # Тип фигуры ("pawn", "knight", etc.)
    color: str                    # Цвет ("white" или "black")
    role: str                     # Роль в паттерне ("attacker", "defender", "target", "support")
    importance: float = 1.0       # Важность фигуры в паттерне (0.0-1.0)
    move_sequence: List[str] = None  # Последовательность ходов для этой фигуры


@dataclass
class ExchangeSequence:
    """Последовательность размена"""
    moves: List[str]              # Последовательность ходов
    material_balance: int         # Материальный баланс после размена
    positional_gain: float        # Позиционная выгода
    evaluation_change: float      # Изменение оценки позиции
    probability: float = 0.8      # Вероятность реализации последовательности


@dataclass
class ChessPatternEnhanced:
    """Улучшенный шахматный паттерн"""
    # Основная информация
    id: str                       # Уникальный идентификатор
    name: str                     # Название паттерна
    description: str              # Описание
    category: PatternCategory     # Категория паттерна
    
    # Позиция и ходы
    fen: str                      # FEN позиции
    key_move: str                 # Ключевой ход (в UCI формате)
    alternative_moves: List[str] = None  # Альтернативные ходы
    
    # Фигуры, участвующие в паттерне
    participating_pieces: List[PatternPiece] = None
    excluded_pieces: List[str] = None  # Фигуры, не участвующие в паттерне (квадраты)
    
    # Размен (если применимо)
    exchange_sequence: ExchangeSequence = None
    exchange_type: ExchangeType = None
    
    # Метаданные
    frequency: float = 1.0        # Частота встречаемости
    success_rate: float = 0.5     # Процент успешного применения
    elo_range: Tuple[int, int] = (800, 2800)  # Диапазон ELO для применения
    game_phase: str = "any"       # Фаза игры ("opening", "middlegame", "endgame", "any")
    
    # Условия применения
    conditions: Dict[str, Any] = None  # Дополнительные условия
    tags: List[str] = None        # Теги для поиска
    
    # Служебная информация
    created_at: str = None        # Дата создания
    updated_at: str = None        # Дата обновления
    author: str = "system"        # Автор паттерна
    enabled: bool = True          # Включен ли паттерн
    
    def __post_init__(self):
        if self.participating_pieces is None:
            self.participating_pieces = []
        if self.alternative_moves is None:
            self.alternative_moves = []
        if self.excluded_pieces is None:
            self.excluded_pieces = []
        if self.conditions is None:
            self.conditions = {}
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at


class PatternManager:
    """Менеджер паттернов"""
    
    def __init__(self, patterns_dir: str = "patterns/enhanced"):
        self.patterns_dir = Path(patterns_dir)
        self.patterns_dir.mkdir(parents=True, exist_ok=True)
        self.patterns: Dict[str, ChessPatternEnhanced] = {}
        self.enabled_categories: Set[PatternCategory] = set(PatternCategory)
        self.load_all_patterns()
    
    def create_pattern(self, pattern: ChessPatternEnhanced) -> bool:
        """Создать новый паттерн"""
        try:
            pattern.created_at = datetime.now().isoformat()
            pattern.updated_at = pattern.created_at
            
            # Сохранить в файл
            pattern_file = self.patterns_dir / f"{pattern.id}.json"
            with open(pattern_file, 'w', encoding='utf-8') as f:
                # Конвертируем в словарь для JSON сериализации
                pattern_dict = self._pattern_to_dict(pattern)
                json.dump(pattern_dict, f, indent=2, ensure_ascii=False)
            
            # Добавить в память
            self.patterns[pattern.id] = pattern
            logger.info(f"Created pattern: {pattern.id} - {pattern.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create pattern {pattern.id}: {e}")
            return False
    
    def load_pattern(self, pattern_id: str) -> Optional[ChessPatternEnhanced]:
        """Загрузить паттерн по ID"""
        pattern_file = self.patterns_dir / f"{pattern_id}.json"
        if not pattern_file.exists():
            return None
        
        try:
            with open(pattern_file, 'r', encoding='utf-8') as f:
                pattern_dict = json.load(f)
            
            pattern = self._dict_to_pattern(pattern_dict)
            self.patterns[pattern.id] = pattern
            return pattern
            
        except Exception as e:
            logger.error(f"Failed to load pattern {pattern_id}: {e}")
            return None
    
    def load_all_patterns(self):
        """Загрузить все паттерны из директории"""
        self.patterns.clear()
        
        for pattern_file in self.patterns_dir.glob("*.json"):
            pattern_id = pattern_file.stem
            pattern = self.load_pattern(pattern_id)
            if pattern:
                self.patterns[pattern_id] = pattern
        
        logger.info(f"Loaded {len(self.patterns)} patterns")
    
    def save_pattern(self, pattern: ChessPatternEnhanced) -> bool:
        """Сохранить изменения в паттерне"""
        try:
            pattern.updated_at = datetime.now().isoformat()
            
            pattern_file = self.patterns_dir / f"{pattern.id}.json"
            with open(pattern_file, 'w', encoding='utf-8') as f:
                pattern_dict = self._pattern_to_dict(pattern)
                json.dump(pattern_dict, f, indent=2, ensure_ascii=False)
            
            self.patterns[pattern.id] = pattern
            return True
            
        except Exception as e:
            logger.error(f"Failed to save pattern {pattern.id}: {e}")
            return False
    
    def delete_pattern(self, pattern_id: str) -> bool:
        """Удалить паттерн"""
        try:
            pattern_file = self.patterns_dir / f"{pattern_id}.json"
            if pattern_file.exists():
                pattern_file.unlink()
            
            if pattern_id in self.patterns:
                del self.patterns[pattern_id]
            
            logger.info(f"Deleted pattern: {pattern_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete pattern {pattern_id}: {e}")
            return False
    
    def get_patterns(
        self,
        categories: List[PatternCategory] = None,
        enabled_only: bool = True,
        elo_range: Tuple[int, int] = None,
        game_phase: str = None,
        tags: List[str] = None
    ) -> List[ChessPatternEnhanced]:
        """Получить паттерны с фильтрацией"""
        
        patterns = list(self.patterns.values())
        
        # Фильтр по включенности
        if enabled_only:
            patterns = [p for p in patterns if p.enabled]
        
        # Фильтр по категориям
        if categories:
            patterns = [p for p in patterns if p.category in categories]
        
        # Фильтр по включенным категориям
        patterns = [p for p in patterns if p.category in self.enabled_categories]
        
        # Фильтр по ELO
        if elo_range:
            min_elo, max_elo = elo_range
            patterns = [p for p in patterns 
                       if p.elo_range[0] <= max_elo and p.elo_range[1] >= min_elo]
        
        # Фильтр по фазе игры
        if game_phase:
            patterns = [p for p in patterns 
                       if p.game_phase == "any" or p.game_phase == game_phase]
        
        # Фильтр по тегам
        if tags:
            patterns = [p for p in patterns 
                       if any(tag in p.tags for tag in tags)]
        
        return patterns
    
    def find_matching_patterns(
        self,
        board: chess.Board,
        max_results: int = 5
    ) -> List[Tuple[ChessPatternEnhanced, float]]:
        """Найти подходящие паттерны для текущей позиции"""
        
        matching_patterns = []
        current_fen = board.fen()
        
        # Определить фазу игры
        game_phase = self._determine_game_phase(board)
        
        # Получить активные паттерны
        active_patterns = self.get_patterns(
            enabled_only=True,
            game_phase=game_phase
        )
        
        for pattern in active_patterns:
            similarity = self._calculate_position_similarity(board, pattern)
            if similarity > 0.3:  # Минимальный порог схожести
                matching_patterns.append((pattern, similarity))
        
        # Сортировать по схожести
        matching_patterns.sort(key=lambda x: x[1], reverse=True)
        
        return matching_patterns[:max_results]
    
    def set_category_enabled(self, category: PatternCategory, enabled: bool):
        """Включить/выключить категорию паттернов"""
        if enabled:
            self.enabled_categories.add(category)
        else:
            self.enabled_categories.discard(category)
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Получить статистику по паттернам"""
        stats = {
            "total_patterns": len(self.patterns),
            "enabled_patterns": len([p for p in self.patterns.values() if p.enabled]),
            "by_category": {},
            "by_game_phase": {},
            "avg_success_rate": 0.0,
            "enabled_categories": [cat.value for cat in self.enabled_categories]
        }
        
        if not self.patterns:
            return stats
        
        # Статистика по категориям
        for pattern in self.patterns.values():
            cat = pattern.category.value
            stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1
            
            phase = pattern.game_phase
            stats["by_game_phase"][phase] = stats["by_game_phase"].get(phase, 0) + 1
        
        # Средний процент успеха
        success_rates = [p.success_rate for p in self.patterns.values()]
        if success_rates:
            stats["avg_success_rate"] = sum(success_rates) / len(success_rates)
        
        return stats
    
    def _pattern_to_dict(self, pattern: ChessPatternEnhanced) -> Dict[str, Any]:
        """Конвертировать паттерн в словарь для JSON"""
        pattern_dict = asdict(pattern)
        
        # Конвертировать enum в строки
        pattern_dict["category"] = pattern.category.value
        if pattern.exchange_type:
            pattern_dict["exchange_type"] = pattern.exchange_type.value
        
        return pattern_dict
    
    def _dict_to_pattern(self, pattern_dict: Dict[str, Any]) -> ChessPatternEnhanced:
        """Конвертировать словарь в паттерн"""
        # Конвертировать строки в enum
        pattern_dict["category"] = PatternCategory(pattern_dict["category"])
        if pattern_dict.get("exchange_type"):
            pattern_dict["exchange_type"] = ExchangeType(pattern_dict["exchange_type"])
        
        # Конвертировать списки PatternPiece
        if pattern_dict.get("participating_pieces"):
            pieces = []
            for piece_data in pattern_dict["participating_pieces"]:
                if isinstance(piece_data, dict):
                    piece = PatternPiece(**piece_data)
                    pieces.append(piece)
            pattern_dict["participating_pieces"] = pieces
        
        # Конвертировать ExchangeSequence
        if pattern_dict.get("exchange_sequence"):
            seq_data = pattern_dict["exchange_sequence"]
            if isinstance(seq_data, dict):
                pattern_dict["exchange_sequence"] = ExchangeSequence(**seq_data)
        
        return ChessPatternEnhanced(**pattern_dict)
    
    def _determine_game_phase(self, board: chess.Board) -> str:
        """Определить фазу игры"""
        # Подсчет материала
        piece_count = 0
        for piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]:
            piece_count += len(board.pieces(piece_type, chess.WHITE))
            piece_count += len(board.pieces(piece_type, chess.BLACK))
        
        if board.fullmove_number <= 12:
            return "opening"
        elif piece_count <= 6:
            return "endgame"
        else:
            return "middlegame"
    
    def _calculate_position_similarity(
        self,
        board: chess.Board,
        pattern: ChessPatternEnhanced
    ) -> float:
        """Вычислить схожесть позиции с паттерном"""
        try:
            pattern_board = chess.Board(pattern.fen)
        except:
            return 0.0
        
        similarity = 0.0
        total_weight = 0.0
        
        # Сравнить участвующие фигуры
        for pattern_piece in pattern.participating_pieces:
            try:
                square = chess.parse_square(pattern_piece.square)
                current_piece = board.piece_at(square)
                
                weight = pattern_piece.importance
                total_weight += weight
                
                if current_piece:
                    # Проверить тип и цвет фигуры
                    piece_type_match = (
                        current_piece.piece_type == 
                        getattr(chess, pattern_piece.piece_type.upper())
                    )
                    color_match = (
                        (current_piece.color == chess.WHITE and pattern_piece.color == "white") or
                        (current_piece.color == chess.BLACK and pattern_piece.color == "black")
                    )
                    
                    if piece_type_match and color_match:
                        similarity += weight
                
            except:
                continue
        
        if total_weight > 0:
            return similarity / total_weight
        else:
            # Fallback: простое сравнение FEN
            return 0.8 if board.fen().split()[0] == pattern.fen.split()[0] else 0.0


class ExchangeAnalyzer:
    """Анализатор размена с предвидением 2-3 ходов"""
    
    def __init__(self):
        self.piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0
        }
    
    def analyze_exchange_patterns(
        self,
        board: chess.Board,
        depth: int = 3
    ) -> List[ExchangeSequence]:
        """Анализировать возможные паттерны размена"""
        
        exchanges = []
        
        # Найти все возможные взятия
        capture_moves = [move for move in board.legal_moves if board.is_capture(move)]
        
        for initial_move in capture_moves:
            sequence = self._analyze_exchange_sequence(board, initial_move, depth)
            if sequence and abs(sequence.material_balance) >= 1:  # Значимый размен
                exchanges.append(sequence)
        
        return exchanges
    
    def _analyze_exchange_sequence(
        self,
        board: chess.Board,
        initial_move: chess.Move,
        depth: int
    ) -> Optional[ExchangeSequence]:
        """Анализировать последовательность размена"""
        
        if depth <= 0:
            return None
        
        # Создать копию доски
        test_board = board.copy()
        moves = [initial_move.uci()]
        material_balance = 0
        
        # Выполнить первый ход
        captured_piece = test_board.piece_at(initial_move.to_square)
        if captured_piece:
            material_balance += self.piece_values[captured_piece.piece_type]
        
        moving_piece = test_board.piece_at(initial_move.from_square)
        if moving_piece:
            material_balance -= self.piece_values[moving_piece.piece_type]
        
        test_board.push(initial_move)
        
        # Анализировать ответные взятия
        for _ in range(depth - 1):
            # Найти лучшее ответное взятие
            recaptures = [
                move for move in test_board.legal_moves 
                if test_board.is_capture(move) and move.to_square == initial_move.to_square
            ]
            
            if not recaptures:
                break
            
            # Выбрать наименее ценную фигуру для взятия
            best_recapture = min(
                recaptures,
                key=lambda m: self.piece_values[test_board.piece_at(m.from_square).piece_type]
            )
            
            # Обновить материальный баланс
            captured = test_board.piece_at(best_recapture.to_square)
            if captured:
                if test_board.turn == chess.WHITE:
                    material_balance += self.piece_values[captured.piece_type]
                else:
                    material_balance -= self.piece_values[captured.piece_type]
            
            moving = test_board.piece_at(best_recapture.from_square)
            if moving:
                if test_board.turn == chess.WHITE:
                    material_balance -= self.piece_values[moving.piece_type]
                else:
                    material_balance += self.piece_values[moving.piece_type]
            
            moves.append(best_recapture.uci())
            test_board.push(best_recapture)
        
        # Вычислить позиционную выгоду (упрощенно)
        positional_gain = self._evaluate_positional_change(board, test_board)
        
        # Оценить вероятность реализации
        probability = max(0.5, 1.0 - len(moves) * 0.1)
        
        return ExchangeSequence(
            moves=moves,
            material_balance=material_balance,
            positional_gain=positional_gain,
            evaluation_change=material_balance * 100 + positional_gain,
            probability=probability
        )
    
    def _evaluate_positional_change(
        self,
        board_before: chess.Board,
        board_after: chess.Board
    ) -> float:
        """Оценить позиционные изменения (упрощенно)"""
        
        # Упрощенная оценка: количество атакованных полей
        before_attacks = len(list(board_before.legal_moves))
        after_attacks = len(list(board_after.legal_moves))
        
        # Безопасность короля
        before_king_safety = self._evaluate_king_safety(board_before)
        after_king_safety = self._evaluate_king_safety(board_after)
        
        return (after_attacks - before_attacks) * 2 + (after_king_safety - before_king_safety) * 5
    
    def _evaluate_king_safety(self, board: chess.Board) -> float:
        """Оценить безопасность короля"""
        safety = 0.0
        
        for color in [chess.WHITE, chess.BLACK]:
            king_square = board.king(color)
            if king_square is not None:
                # Количество атакующих фигур противника
                attackers = len(board.attackers(not color, king_square))
                # Количество защитников
                defenders = len(board.attackers(color, king_square))
                
                color_multiplier = 1 if color == chess.WHITE else -1
                safety += (defenders - attackers) * color_multiplier
        
        return safety


def create_default_patterns() -> List[ChessPatternEnhanced]:
    """Создать набор паттернов по умолчанию"""
    
    patterns = []
    
    # Тактический паттерн: Вилка конём
    knight_fork = ChessPatternEnhanced(
        id="knight_fork_basic",
        name="Вилка конём",
        description="Конь атакует две или более фигуры одновременно",
        category=PatternCategory.TACTICAL,
        fen="r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 4",
        key_move="Nd4",
        participating_pieces=[
            PatternPiece("f3", "knight", "white", "attacker", 1.0),
            PatternPiece("e8", "king", "black", "target", 0.9),
            PatternPiece("c6", "knight", "black", "target", 0.8)
        ],
        frequency=0.3,
        success_rate=0.75,
        game_phase="middlegame",
        tags=["fork", "knight", "tactical"]
    )
    patterns.append(knight_fork)
    
    # Паттерн размена: Выгодный размен в эндшпиле
    favorable_exchange = ChessPatternEnhanced(
        id="favorable_endgame_exchange",
        name="Выгодный размен в эндшпиле",
        description="Размен, упрощающий позицию в выгодном эндшпиле",
        category=PatternCategory.EXCHANGE,
        fen="8/8/8/3k4/8/3K4/3R4/8 w - - 0 1",
        key_move="Rd5+",
        exchange_type=ExchangeType.FAVORABLE_TRADE,
        exchange_sequence=ExchangeSequence(
            moves=["Rd5+", "Kxd5"],
            material_balance=0,
            positional_gain=50.0,
            evaluation_change=50.0,
            probability=0.9
        ),
        participating_pieces=[
            PatternPiece("d2", "rook", "white", "attacker", 1.0),
            PatternPiece("d5", "king", "black", "target", 0.9)
        ],
        frequency=0.4,
        success_rate=0.8,
        game_phase="endgame",
        tags=["exchange", "endgame", "simplification"]
    )
    patterns.append(favorable_exchange)
    
    # Дебютный паттерн
    italian_game = ChessPatternEnhanced(
        id="italian_game_development",
        name="Развитие в итальянской партии",
        description="Быстрое развитие фигур в итальянской партии",
        category=PatternCategory.OPENING,
        fen="r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
        key_move="Be7",
        participating_pieces=[
            PatternPiece("c4", "bishop", "white", "attacker", 0.9),
            PatternPiece("f3", "knight", "white", "support", 0.8),
            PatternPiece("c8", "bishop", "black", "defender", 0.7)
        ],
        frequency=0.6,
        success_rate=0.65,
        game_phase="opening",
        tags=["italian", "development", "opening"]
    )
    patterns.append(italian_game)
    
    return patterns


# Пример использования
if __name__ == "__main__":
    # Создать менеджер паттернов
    manager = PatternManager()
    
    # Создать паттерны по умолчанию
    default_patterns = create_default_patterns()
    for pattern in default_patterns:
        manager.create_pattern(pattern)
    
    # Показать статистику
    stats = manager.get_pattern_statistics()
    print("Pattern Statistics:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))