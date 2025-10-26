#!/usr/bin/env python3
"""
Enhanced Chess Pattern System

Усовершенствованная система паттернов с:
1. Управлением выбором паттернов
2. Усложненным определением паттернов (отсечение неучаствующих фигур)
3. Анализом разменов на 2-3 хода вперед
4. Отдельными JSON файлами для каждого паттерна
"""

import sys
import time
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, Counter
import copy

# Chess imports with fallbacks
try:
    import chess
    CHESS_AVAILABLE = True
except ImportError:
    chess = None
    CHESS_AVAILABLE = False

logger = logging.getLogger(__name__)

class PatternRole(Enum):
    """Роли фигур в паттерне"""
    ATTACKER = "attacker"          # Атакующая фигура
    TARGET = "target"              # Цель атаки
    DEFENDER = "defender"          # Защищающая фигура
    SUPPORTER = "supporter"        # Поддерживающая фигура
    BLOCKER = "blocker"           # Блокирующая фигура
    SACRIFICE = "sacrifice"        # Жертвуемая фигура
    DECOY = "decoy"               # Приманка
    EXCLUDED = "excluded"          # Исключенная (не участвует)

class ExchangeType(Enum):
    """Типы разменов"""
    EQUAL_EXCHANGE = "equal"       # Равный размен
    FAVORABLE_EXCHANGE = "favorable" # Выгодный размен
    SACRIFICE = "sacrifice"        # Жертва
    POSITIONAL_EXCHANGE = "positional" # Позиционный размен
    MATERIAL_GAIN = "material_gain" # Выигрыш материала

@dataclass
class ParticipatingPiece:
    """Фигура, участвующая в паттерне"""
    square: str
    piece: str
    role: PatternRole
    influence: float  # 0.0 - 1.0, насколько важна для паттерна
    move_number: Optional[int] = None  # На каком ходу участвует
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "square": self.square,
            "piece": self.piece,
            "role": self.role.value,
            "influence": self.influence,
            "move_number": self.move_number
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParticipatingPiece':
        return cls(
            square=data["square"],
            piece=data["piece"],
            role=PatternRole(data["role"]),
            influence=data["influence"],
            move_number=data.get("move_number")
        )

@dataclass
class ExchangeMove:
    """Ход в размене"""
    move_san: str
    move_uci: str
    capture: Optional[str]
    material_change: int  # Изменение материала
    positional_value: float  # Позиционная оценка
    special_flags: List[str]  # check, discovered_check, pin, etc.
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExchangeMove':
        return cls(**data)

@dataclass
class ExchangeSequence:
    """Последовательность размена"""
    exchange_type: ExchangeType
    moves_ahead: int
    sequence: List[ExchangeMove]
    net_material: int
    positional_gain: float
    total_evaluation: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "exchange_type": self.exchange_type.value,
            "moves_ahead": self.moves_ahead,
            "sequence": [move.to_dict() for move in self.sequence],
            "net_material": self.net_material,
            "positional_gain": self.positional_gain,
            "total_evaluation": self.total_evaluation
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExchangeSequence':
        return cls(
            exchange_type=ExchangeType(data["exchange_type"]),
            moves_ahead=data["moves_ahead"],
            sequence=[ExchangeMove.from_dict(m) for m in data["sequence"]],
            net_material=data["net_material"],
            positional_gain=data["positional_gain"],
            total_evaluation=data["total_evaluation"]
        )

@dataclass
class EnhancedChessPattern:
    """Усовершенствованный шахматный паттерн"""
    # Основная информация
    pattern_id: str
    name: str
    description: str
    created_at: str
    updated_at: str
    author: str
    
    # Позиция и ход
    fen_before: str
    fen_after: str
    key_move_san: str
    key_move_uci: str
    
    # Участвующие фигуры
    participating_pieces: List[ParticipatingPiece]
    excluded_squares: List[str]
    
    # Категоризация
    primary_category: str
    secondary_categories: List[str]
    game_phase: str
    complexity: str
    tags: List[str]
    difficulty_rating: float
    
    # Анализ
    alternatives: Dict[str, Any]
    game_context: Dict[str, Any]
    exchange_sequence: Optional[ExchangeSequence]
    
    # Визуализация
    highlighted_squares: List[str]
    arrows: List[Dict[str, Any]]
    heatmap_data: Dict[str, float]
    
    # Метаданные
    detection_confidence: float
    pattern_frequency: str
    learning_value: float
    bot_evaluations: Dict[str, Any]
    human_annotations: Dict[str, Any]
    related_patterns: Dict[str, List[str]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для JSON"""
        return {
            "pattern_id": self.pattern_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "author": self.author,
            
            "position": {
                "fen_before": self.fen_before,
                "fen_after": self.fen_after,
                "key_move": {
                    "san": self.key_move_san,
                    "uci": self.key_move_uci,
                    "from_square": self.key_move_uci[:2],
                    "to_square": self.key_move_uci[2:4]
                }
            },
            
            "participating_pieces": {
                "primary_pieces": [p.to_dict() for p in self.participating_pieces 
                                 if p.role in [PatternRole.ATTACKER, PatternRole.TARGET]],
                "supporting_pieces": [p.to_dict() for p in self.participating_pieces 
                                    if p.role in [PatternRole.DEFENDER, PatternRole.SUPPORTER, 
                                                PatternRole.BLOCKER, PatternRole.DECOY]],
                "excluded_pieces": self.excluded_squares
            },
            
            "categories": {
                "primary": self.primary_category,
                "secondary": self.secondary_categories,
                "game_phase": self.game_phase,
                "complexity": self.complexity
            },
            "tags": self.tags,
            "difficulty_rating": self.difficulty_rating,
            
            "alternatives": self.alternatives,
            "game_context": self.game_context,
            "exchange_sequence": self.exchange_sequence.to_dict() if self.exchange_sequence else None,
            
            "visualization": {
                "highlighted_squares": self.highlighted_squares,
                "arrows": self.arrows,
                "heatmap_data": self.heatmap_data
            },
            
            "metadata": {
                "detection_confidence": self.detection_confidence,
                "pattern_frequency": self.pattern_frequency,
                "learning_value": self.learning_value,
                "bot_evaluations": self.bot_evaluations,
                "human_annotations": self.human_annotations
            },
            
            "related_patterns": self.related_patterns
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnhancedChessPattern':
        """Создание из словаря"""
        # Извлекаем участвующие фигуры
        participating_pieces = []
        if "participating_pieces" in data:
            for piece_data in data["participating_pieces"].get("primary_pieces", []):
                participating_pieces.append(ParticipatingPiece.from_dict(piece_data))
            for piece_data in data["participating_pieces"].get("supporting_pieces", []):
                participating_pieces.append(ParticipatingPiece.from_dict(piece_data))
        
        # Извлекаем размен
        exchange_sequence = None
        if data.get("exchange_sequence"):
            exchange_sequence = ExchangeSequence.from_dict(data["exchange_sequence"])
        
        return cls(
            pattern_id=data["pattern_id"],
            name=data["name"],
            description=data["description"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            author=data["author"],
            
            fen_before=data["position"]["fen_before"],
            fen_after=data["position"]["fen_after"],
            key_move_san=data["position"]["key_move"]["san"],
            key_move_uci=data["position"]["key_move"]["uci"],
            
            participating_pieces=participating_pieces,
            excluded_squares=data["participating_pieces"].get("excluded_pieces", []),
            
            primary_category=data["categories"]["primary"],
            secondary_categories=data["categories"]["secondary"],
            game_phase=data["categories"]["game_phase"],
            complexity=data["categories"]["complexity"],
            tags=data["tags"],
            difficulty_rating=data["difficulty_rating"],
            
            alternatives=data["alternatives"],
            game_context=data["game_context"],
            exchange_sequence=exchange_sequence,
            
            highlighted_squares=data["visualization"]["highlighted_squares"],
            arrows=data["visualization"]["arrows"],
            heatmap_data=data["visualization"]["heatmap_data"],
            
            detection_confidence=data["metadata"]["detection_confidence"],
            pattern_frequency=data["metadata"]["pattern_frequency"],
            learning_value=data["metadata"]["learning_value"],
            bot_evaluations=data["metadata"]["bot_evaluations"],
            human_annotations=data["metadata"]["human_annotations"],
            related_patterns=data["related_patterns"]
        )

class EnhancedPatternDetector:
    """Усовершенствованный детектор паттернов"""
    
    def __init__(self):
        self.min_alternatives = 3
        self.confidence_threshold = 0.6
        self.evaluation_threshold = 0.5
        self.exchange_depth = 3  # Глубина анализа разменов
        
    def analyze_position_enhanced(self, board, chosen_move, bot_name: str, 
                                bot_evaluation: Dict[str, Any],
                                all_bot_results: Dict[str, Dict[str, Any]]) -> Optional[EnhancedChessPattern]:
        """Усовершенствованный анализ позиции"""
        
        # Базовый анализ
        legal_moves = list(board.legal_moves)
        if len(legal_moves) < self.min_alternatives:
            return None
        
        # Определяем участвующие фигуры
        participating_pieces = self._identify_participating_pieces(board, chosen_move)
        
        # Определяем исключенные поля
        excluded_squares = self._identify_excluded_squares(board, participating_pieces)
        
        # Анализируем размены
        exchange_sequence = self._analyze_exchange_sequence(board, chosen_move)
        
        # Определяем категории
        categories = self._detect_enhanced_categories(board, chosen_move, exchange_sequence)
        
        if not categories:
            return None
        
        # Создаем паттерн
        pattern_id = self._generate_pattern_id(board, chosen_move)
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        
        # Визуализация
        highlighted_squares = [p.square for p in participating_pieces if p.role != PatternRole.EXCLUDED]
        arrows = self._generate_arrows(board, chosen_move, participating_pieces)
        heatmap_data = self._calculate_enhanced_heatmap(board, participating_pieces)
        
        return EnhancedChessPattern(
            pattern_id=pattern_id,
            name=self._generate_pattern_name(categories, chosen_move),
            description=self._generate_pattern_description(board, chosen_move, categories),
            created_at=timestamp,
            updated_at=timestamp,
            author="EnhancedPatternDetector_v2.0",
            
            fen_before=board.fen(),
            fen_after=self._get_fen_after_move(board, chosen_move),
            key_move_san=board.san(chosen_move),
            key_move_uci=chosen_move.uci(),
            
            participating_pieces=participating_pieces,
            excluded_squares=excluded_squares,
            
            primary_category=categories[0] if categories else "unknown",
            secondary_categories=categories[1:],
            game_phase=self._detect_game_phase(board),
            complexity=self._assess_complexity(participating_pieces, exchange_sequence),
            tags=[],
            difficulty_rating=self._calculate_difficulty_rating(participating_pieces, exchange_sequence),
            
            alternatives=self._analyze_alternatives_enhanced(board, legal_moves, chosen_move),
            game_context=self._extract_game_context(board),
            exchange_sequence=exchange_sequence,
            
            highlighted_squares=highlighted_squares,
            arrows=arrows,
            heatmap_data=heatmap_data,
            
            detection_confidence=self._calculate_confidence_enhanced(participating_pieces, exchange_sequence),
            pattern_frequency="unknown",
            learning_value=self._calculate_learning_value(categories, exchange_sequence),
            bot_evaluations={bot_name: bot_evaluation, **all_bot_results},
            human_annotations={"verified": False, "notes": ""},
            related_patterns={"similar_patterns": [], "counter_patterns": [], "follow_up_patterns": []}
        )
    
    def _identify_participating_pieces(self, board, move) -> List[ParticipatingPiece]:
        """Определяет фигуры, участвующие в паттерне"""
        participating = []
        
        # Основная атакующая фигура
        moving_piece = board.piece_at(move.from_square)
        if moving_piece:
            participating.append(ParticipatingPiece(
                square=chess.square_name(move.from_square),
                piece=moving_piece.symbol(),
                role=PatternRole.ATTACKER,
                influence=1.0
            ))
        
        # Цель атаки
        target_piece = board.piece_at(move.to_square)
        if target_piece:
            participating.append(ParticipatingPiece(
                square=chess.square_name(move.to_square),
                piece=target_piece.symbol(),
                role=PatternRole.TARGET,
                influence=0.9
            ))
        
        # Анализируем атаки с новой позиции
        board_copy = board.copy()
        board_copy.push(move)
        
        # Фигуры под атакой с новой позиции
        attacked_squares = board_copy.attacks(move.to_square)
        for square in attacked_squares:
            piece = board_copy.piece_at(square)
            if piece and piece.color != moving_piece.color:
                # Проверяем важность цели
                piece_value = self._get_piece_value(piece.piece_type)
                if piece_value >= 3:  # Ладья, ферзь, король
                    participating.append(ParticipatingPiece(
                        square=chess.square_name(square),
                        piece=piece.symbol(),
                        role=PatternRole.TARGET,
                        influence=min(0.8, piece_value / 9.0)
                    ))
        
        # Защищающие фигуры
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color == moving_piece.color and square != move.from_square:
                # Проверяем, защищает ли эта фигура атакующую
                if board.is_attacked_by(piece.color, move.to_square):
                    defenders = board.attackers(piece.color, move.to_square)
                    if square in defenders:
                        participating.append(ParticipatingPiece(
                            square=chess.square_name(square),
                            piece=piece.symbol(),
                            role=PatternRole.SUPPORTER,
                            influence=0.6
                        ))
        
        return participating
    
    def _identify_excluded_squares(self, board, participating_pieces: List[ParticipatingPiece]) -> List[str]:
        """Определяет поля, которые не участвуют в паттерне"""
        participating_squares = {p.square for p in participating_pieces}
        excluded = []
        
        for square in chess.SQUARES:
            square_name = chess.square_name(square)
            piece = board.piece_at(square)
            
            # Если есть фигура, но она не участвует в паттерне
            if piece and square_name not in participating_squares:
                # Проверяем, влияет ли фигура на паттерн
                if not self._piece_influences_pattern(board, square, participating_squares):
                    excluded.append(square_name)
        
        return excluded
    
    def _piece_influences_pattern(self, board, square: int, pattern_squares: Set[str]) -> bool:
        """Проверяет, влияет ли фигура на паттерн"""
        piece = board.piece_at(square)
        if not piece:
            return False
        
        # Проверяем атаки на ключевые поля паттерна
        attacks = board.attacks(square)
        for attack_square in attacks:
            if chess.square_name(attack_square) in pattern_squares:
                return True
        
        # Проверяем защиту ключевых полей
        for pattern_square_name in pattern_squares:
            pattern_square = chess.parse_square(pattern_square_name)
            if board.is_attacked_by(piece.color, pattern_square):
                defenders = board.attackers(piece.color, pattern_square)
                if square in defenders:
                    return True
        
        return False
    
    def _analyze_exchange_sequence(self, board, initial_move) -> Optional[ExchangeSequence]:
        """Анализирует последовательность размена на несколько ходов вперед"""
        if not board.is_capture(initial_move):
            return None
        
        sequence = []
        board_copy = board.copy()
        current_move = initial_move
        total_material = 0
        total_positional = 0.0
        
        for depth in range(self.exchange_depth):
            if not current_move or not board_copy.is_legal(current_move):
                break
            
            # Анализируем текущий ход
            captured_piece = board_copy.piece_at(current_move.to_square)
            material_change = 0
            
            if captured_piece:
                material_change = self._get_piece_value(captured_piece.piece_type)
                if board_copy.turn == chess.BLACK:  # Если ход черных, материал для них положительный
                    material_change = -material_change
            
            # Определяем специальные флаги
            special_flags = []
            if board_copy.gives_check(current_move):
                special_flags.append("check")
            if self._is_discovered_check(board_copy, current_move):
                special_flags.append("discovered_check")
            if self._creates_pin(board_copy, current_move):
                special_flags.append("pin")
            
            # Добавляем ход в последовательность
            exchange_move = ExchangeMove(
                move_san=board_copy.san(current_move),
                move_uci=current_move.uci(),
                capture=captured_piece.symbol() if captured_piece else None,
                material_change=material_change,
                positional_value=self._evaluate_positional_change(board_copy, current_move),
                special_flags=special_flags
            )
            sequence.append(exchange_move)
            
            # Применяем ход
            board_copy.push(current_move)
            total_material += material_change
            total_positional += exchange_move.positional_value
            
            # Ищем следующий размен (рекапчур)
            next_move = self._find_recapture(board_copy, current_move.to_square)
            if not next_move:
                break
            
            current_move = next_move
        
        if not sequence:
            return None
        
        # Определяем тип размена
        exchange_type = self._classify_exchange_type(total_material, total_positional)
        
        return ExchangeSequence(
            exchange_type=exchange_type,
            moves_ahead=len(sequence),
            sequence=sequence,
            net_material=total_material,
            positional_gain=total_positional,
            total_evaluation=total_material + total_positional
        )
    
    def _find_recapture(self, board, target_square: int):
        """Находит рекапчур на указанном поле"""
        # Ищем ходы, которые атакуют поле где произошел захват
        for move in board.legal_moves:
            if move.to_square == target_square and board.is_capture(move):
                return move
        return None
    
    def _classify_exchange_type(self, material: int, positional: float) -> ExchangeType:
        """Классифицирует тип размена"""
        if abs(material) <= 1 and abs(positional) <= 0.5:
            return ExchangeType.EQUAL_EXCHANGE
        elif material > 1 or (material >= 0 and positional > 1.0):
            return ExchangeType.FAVORABLE_EXCHANGE
        elif material < -2:
            return ExchangeType.SACRIFICE
        elif abs(material) <= 1 and abs(positional) > 1.0:
            return ExchangeType.POSITIONAL_EXCHANGE
        elif material > 0:
            return ExchangeType.MATERIAL_GAIN
        else:
            return ExchangeType.EQUAL_EXCHANGE
    
    def _get_piece_value(self, piece_type) -> int:
        """Получает стоимость фигуры"""
        values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0  # Король не имеет материальной стоимости
        }
        return values.get(piece_type, 0)
    
    def _is_discovered_check(self, board, move) -> bool:
        """Проверяет, создает ли ход вскрытый шах"""
        # Упрощенная проверка
        board_copy = board.copy()
        board_copy.push(move)
        return board_copy.is_check()
    
    def _creates_pin(self, board, move) -> bool:
        """Проверяет, создает ли ход связку"""
        # Упрощенная проверка связки
        return False  # Требует более сложной логики
    
    def _evaluate_positional_change(self, board, move) -> float:
        """Оценивает позиционное изменение от хода"""
        # Упрощенная позиционная оценка
        positional_value = 0.0
        
        # Централизация
        to_square = move.to_square
        center_distance = min(abs(chess.square_file(to_square) - 3.5), 
                             abs(chess.square_rank(to_square) - 3.5))
        positional_value += (3.5 - center_distance) * 0.1
        
        # Активность фигуры
        piece = board.piece_at(move.from_square)
        if piece:
            board_copy = board.copy()
            board_copy.push(move)
            attacks_after = len(board_copy.attacks(move.to_square))
            attacks_before = len(board.attacks(move.from_square))
            positional_value += (attacks_after - attacks_before) * 0.05
        
        return positional_value
    
    def _detect_enhanced_categories(self, board, move, exchange_sequence) -> List[str]:
        """Определяет категории паттерна с учетом разменов"""
        categories = []
        
        # Базовые категории
        if board.is_capture(move):
            categories.append("tactical")
        
        if exchange_sequence:
            if exchange_sequence.exchange_type == ExchangeType.SACRIFICE:
                categories.append("sacrifice")
            elif exchange_sequence.exchange_type == ExchangeType.FAVORABLE_EXCHANGE:
                categories.append("favorable_exchange")
            categories.append("exchange_pattern")
        
        # Фазы игры
        if board.fullmove_number <= 10:
            categories.append("opening")
        elif board.fullmove_number <= 25:
            categories.append("middlegame")
        else:
            categories.append("endgame")
        
        # Тактические мотивы
        if self._is_fork_move(board, move):
            categories.append("fork")
        
        if self._is_pin_move(board, move):
            categories.append("pin")
        
        return categories
    
    def _is_fork_move(self, board, move) -> bool:
        """Проверяет, создает ли ход вилку"""
        board_copy = board.copy()
        board_copy.push(move)
        
        attacking_piece = board_copy.piece_at(move.to_square)
        if not attacking_piece:
            return False
        
        attacked_squares = board_copy.attacks(move.to_square)
        valuable_targets = 0
        
        for square in attacked_squares:
            piece = board_copy.piece_at(square)
            if piece and piece.color != attacking_piece.color:
                if piece.piece_type in [chess.QUEEN, chess.ROOK, chess.KING]:
                    valuable_targets += 1
        
        return valuable_targets >= 2
    
    def _is_pin_move(self, board, move) -> bool:
        """Проверяет, создает ли ход связку"""
        # Упрощенная проверка связки
        return False
    
    def _generate_pattern_name(self, categories: List[str], move) -> str:
        """Генерирует название паттерна"""
        if "fork" in categories:
            return f"Вилка {move.uci()}"
        elif "sacrifice" in categories:
            return f"Жертва {move.uci()}"
        elif "exchange_pattern" in categories:
            return f"Размен {move.uci()}"
        elif "tactical" in categories:
            return f"Тактический удар {move.uci()}"
        else:
            return f"Паттерн {move.uci()}"
    
    def _generate_pattern_description(self, board, move, categories: List[str]) -> str:
        """Генерирует описание паттерна"""
        piece = board.piece_at(move.from_square)
        piece_name = self._get_piece_name(piece.piece_type) if piece else "фигура"
        
        if "fork" in categories:
            return f"{piece_name} с {move.from_square} создает вилку на {move.to_square}"
        elif "sacrifice" in categories:
            return f"Жертва {piece_name} на {move.to_square} для получения преимущества"
        elif "exchange_pattern" in categories:
            return f"Размен начинающийся с {piece_name} на {move.to_square}"
        else:
            return f"{piece_name} идет с {move.from_square} на {move.to_square}"
    
    def _get_piece_name(self, piece_type) -> str:
        """Получает название фигуры на русском"""
        names = {
            chess.PAWN: "пешка",
            chess.KNIGHT: "конь", 
            chess.BISHOP: "слон",
            chess.ROOK: "ладья",
            chess.QUEEN: "ферзь",
            chess.KING: "король"
        }
        return names.get(piece_type, "фигура")
    
    def _generate_arrows(self, board, move, participating_pieces: List[ParticipatingPiece]) -> List[Dict[str, Any]]:
        """Генерирует стрелки для визуализации"""
        arrows = []
        
        # Основная атака
        arrows.append({
            "from": chess.square_name(move.from_square),
            "to": chess.square_name(move.to_square),
            "color": "red",
            "type": "attack"
        })
        
        # Угрозы с новой позиции
        board_copy = board.copy()
        board_copy.push(move)
        
        attacked_squares = board_copy.attacks(move.to_square)
        for square in attacked_squares:
            piece = board_copy.piece_at(square)
            if piece and piece.color != board.turn:
                arrows.append({
                    "from": chess.square_name(move.to_square),
                    "to": chess.square_name(square),
                    "color": "orange",
                    "type": "threat"
                })
        
        return arrows
    
    def _calculate_enhanced_heatmap(self, board, participating_pieces: List[ParticipatingPiece]) -> Dict[str, float]:
        """Вычисляет улучшенную тепловую карту"""
        heatmap = {}
        
        for piece in participating_pieces:
            if piece.role != PatternRole.EXCLUDED:
                heatmap[piece.square] = piece.influence
        
        return heatmap
    
    def _get_fen_after_move(self, board, move) -> str:
        """Получает FEN после хода"""
        board_copy = board.copy()
        board_copy.push(move)
        return board_copy.fen()
    
    def _detect_game_phase(self, board) -> str:
        """Определяет фазу игры"""
        piece_count = len([p for p in board.piece_map().values() if p.piece_type != chess.KING])
        
        if piece_count >= 20:
            return "opening"
        elif piece_count >= 12:
            return "middlegame"
        else:
            return "endgame"
    
    def _assess_complexity(self, participating_pieces: List[ParticipatingPiece], 
                          exchange_sequence: Optional[ExchangeSequence]) -> str:
        """Оценивает сложность паттерна"""
        complexity_score = len(participating_pieces)
        
        if exchange_sequence:
            complexity_score += exchange_sequence.moves_ahead * 2
        
        if complexity_score <= 3:
            return "simple"
        elif complexity_score <= 6:
            return "intermediate"
        else:
            return "complex"
    
    def _calculate_difficulty_rating(self, participating_pieces: List[ParticipatingPiece],
                                   exchange_sequence: Optional[ExchangeSequence]) -> float:
        """Вычисляет рейтинг сложности (1-10)"""
        rating = len(participating_pieces) * 1.5
        
        if exchange_sequence:
            rating += exchange_sequence.moves_ahead * 1.0
            if exchange_sequence.exchange_type == ExchangeType.SACRIFICE:
                rating += 2.0
        
        return min(10.0, max(1.0, rating))
    
    def _analyze_alternatives_enhanced(self, board, legal_moves, chosen_move) -> Dict[str, Any]:
        """Расширенный анализ альтернатив"""
        alternatives = []
        
        for move in legal_moves[:5]:  # Топ 5 альтернатив
            if move == chosen_move:
                continue
            
            # Простая оценка альтернативы
            board_copy = board.copy()
            board_copy.push(move)
            
            alternative = {
                "move": board.san(move),
                "uci": move.uci(),
                "is_capture": board.is_capture(move),
                "is_check": board_copy.is_check(),
                "evaluation": 0.0,  # Placeholder
                "reason": self._get_move_reason(board, move)
            }
            alternatives.append(alternative)
        
        return {
            "considered_moves": alternatives,
            "best_defense": None  # Можно добавить анализ лучшей защиты
        }
    
    def _get_move_reason(self, board, move) -> str:
        """Получает причину хода"""
        if board.is_capture(move):
            return "Захват материала"
        
        board_copy = board.copy()
        board_copy.push(move)
        if board_copy.is_check():
            return "Шах"
        
        # Централизация
        to_square = move.to_square
        if chess.square_file(to_square) in [3, 4] and chess.square_rank(to_square) in [3, 4]:
            return "Централизация"
        
        return "Позиционное улучшение"
    
    def _extract_game_context(self, board) -> Dict[str, Any]:
        """Извлекает контекст игры"""
        return {
            "move_number": board.fullmove_number,
            "turn": "white" if board.turn == chess.WHITE else "black",
            "material_balance": self._calculate_material_balance(board),
            "castling_rights": str(board.castling_rights),
            "game_phase": self._detect_game_phase(board),
            "evaluation_before": 0.0,  # Placeholder
            "evaluation_after": 0.0,   # Placeholder
            "evaluation_swing": 0.0    # Placeholder
        }
    
    def _calculate_material_balance(self, board) -> int:
        """Вычисляет материальный баланс"""
        balance = 0
        piece_values = {
            chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
            chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0
        }
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = piece_values[piece.piece_type]
                balance += value if piece.color == chess.WHITE else -value
        
        return balance
    
    def _calculate_confidence_enhanced(self, participating_pieces: List[ParticipatingPiece],
                                     exchange_sequence: Optional[ExchangeSequence]) -> float:
        """Вычисляет улучшенную уверенность в паттерне"""
        confidence = 0.5  # Базовая уверенность
        
        # Бонус за количество участвующих фигур
        confidence += len(participating_pieces) * 0.1
        
        # Бонус за размены
        if exchange_sequence:
            confidence += 0.2
            if exchange_sequence.moves_ahead >= 3:
                confidence += 0.1
        
        # Бонус за высокое влияние фигур
        max_influence = max((p.influence for p in participating_pieces), default=0)
        confidence += max_influence * 0.2
        
        return min(1.0, confidence)
    
    def _calculate_learning_value(self, categories: List[str], 
                                exchange_sequence: Optional[ExchangeSequence]) -> float:
        """Вычисляет обучающую ценность паттерна"""
        value = 5.0  # Базовая ценность
        
        # Бонус за тактические элементы
        tactical_categories = ["fork", "pin", "sacrifice", "tactical"]
        tactical_count = sum(1 for cat in categories if cat in tactical_categories)
        value += tactical_count * 1.5
        
        # Бонус за размены
        if exchange_sequence:
            value += 2.0
            if exchange_sequence.exchange_type == ExchangeType.SACRIFICE:
                value += 1.5
        
        return min(10.0, value)
    
    def _generate_pattern_id(self, board, move) -> str:
        """Генерирует уникальный ID паттерна"""
        pattern_string = f"{board.fen()}_{move.uci()}_{time.time()}"
        return hashlib.md5(pattern_string.encode()).hexdigest()[:12]

class EnhancedPatternStorage:
    """Усовершенствованное хранилище паттернов с отдельными JSON файлами"""
    
    def __init__(self, storage_path: str = "patterns"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.patterns_index = {}  # ID -> filename mapping
        self.load_patterns_index()
    
    def save_pattern(self, pattern: EnhancedChessPattern):
        """Сохраняет паттерн в отдельный JSON файл"""
        filename = f"{pattern.pattern_id}.json"
        filepath = self.storage_path / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(pattern.to_dict(), f, indent=2, ensure_ascii=False)
            
            # Обновляем индекс
            self.patterns_index[pattern.pattern_id] = filename
            self._save_patterns_index()
            
            logger.info(f"Pattern {pattern.pattern_id} saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save pattern {pattern.pattern_id}: {e}")
    
    def load_pattern(self, pattern_id: str) -> Optional[EnhancedChessPattern]:
        """Загружает паттерн по ID"""
        if pattern_id not in self.patterns_index:
            return None
        
        filename = self.patterns_index[pattern_id]
        filepath = self.storage_path / filename
        
        if not filepath.exists():
            logger.warning(f"Pattern file {filename} not found")
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return EnhancedChessPattern.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load pattern {pattern_id}: {e}")
            return None
    
    def delete_pattern(self, pattern_id: str):
        """Удаляет паттерн"""
        if pattern_id not in self.patterns_index:
            return
        
        filename = self.patterns_index[pattern_id]
        filepath = self.storage_path / filename
        
        try:
            if filepath.exists():
                filepath.unlink()
            
            del self.patterns_index[pattern_id]
            self._save_patterns_index()
            
            logger.info(f"Pattern {pattern_id} deleted")
        except Exception as e:
            logger.error(f"Failed to delete pattern {pattern_id}: {e}")
    
    def get_all_pattern_ids(self) -> List[str]:
        """Получает все ID паттернов"""
        return list(self.patterns_index.keys())
    
    def get_patterns_by_category(self, category: str) -> List[str]:
        """Получает ID паттернов по категории"""
        matching_ids = []
        
        for pattern_id in self.patterns_index.keys():
            pattern = self.load_pattern(pattern_id)
            if pattern and (category in pattern.secondary_categories or 
                           pattern.primary_category == category):
                matching_ids.append(pattern_id)
        
        return matching_ids
    
    def search_patterns(self, query: str) -> List[str]:
        """Поиск паттернов по запросу"""
        query_lower = query.lower()
        matching_ids = []
        
        for pattern_id in self.patterns_index.keys():
            pattern = self.load_pattern(pattern_id)
            if pattern:
                if (query_lower in pattern.name.lower() or
                    query_lower in pattern.description.lower() or
                    any(query_lower in tag.lower() for tag in pattern.tags)):
                    matching_ids.append(pattern_id)
        
        return matching_ids
    
    def load_patterns_index(self):
        """Загружает индекс паттернов"""
        index_file = self.storage_path / "patterns_index.json"
        
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    self.patterns_index = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load patterns index: {e}")
                self.patterns_index = {}
        
        # Сканируем директорию на предмет новых файлов
        self._scan_pattern_files()
    
    def _scan_pattern_files(self):
        """Сканирует файлы паттернов в директории"""
        for filepath in self.storage_path.glob("*.json"):
            if filepath.name == "patterns_index.json":
                continue
            
            pattern_id = filepath.stem
            if pattern_id not in self.patterns_index:
                self.patterns_index[pattern_id] = filepath.name
        
        self._save_patterns_index()
    
    def _save_patterns_index(self):
        """Сохраняет индекс паттернов"""
        index_file = self.storage_path / "patterns_index.json"
        
        try:
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(self.patterns_index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save patterns index: {e}")

# Пример использования
if __name__ == "__main__":
    # Тестируем систему
    detector = EnhancedPatternDetector()
    storage = EnhancedPatternStorage()
    
    print(f"Enhanced pattern system initialized")
    print(f"Loaded {len(storage.get_all_pattern_ids())} existing patterns")
    
    # Можно добавить тестовые паттерны
    print("Enhanced pattern system ready for use!")