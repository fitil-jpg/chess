"""

This module provides advanced pattern detection including:
1. Piece participation tracking (only pieces involved in pattern)
2. Exchange detection and evaluation (2-3 moves ahead)
3. Individual JSON storage for each pattern
4. Pattern filtering and management
Enhanced Pattern Detector

Улучшенный детектор паттернов с фильтрацией неучаствующих фигур
и анализом размена с предвидением 2-3 ходов.
"""

from __future__ import annotations
import chess
from typing import List, Dict, Any, Optional, Set, Tuple
import logging
from dataclasses import dataclass

from chess_ai.enhanced_pattern_system import (
    ChessPatternEnhanced, PatternPiece, ExchangeSequence, 
    PatternCategory, ExchangeType, PatternManager, ExchangeAnalyzer
)

logger = logging.getLogger(__name__)


@dataclass
class PatternMatch:
    """Результат сопоставления паттерна"""
    pattern: ChessPatternEnhanced
    confidence: float                    # Уверенность в совпадении (0.0-1.0)
    relevant_pieces: List[PatternPiece] # Фигуры, участвующие в паттерне
    filtered_pieces: List[str]          # Отфильтрованные фигуры (не участвуют)
    suggested_move: str                 # Предлагаемый ход
    alternative_moves: List[str]        # Альтернативные ходы
    explanation: str                    # Объяснение паттерна


class EnhancedPatternDetector:
    """Улучшенный детектор паттернов"""
    
    def __init__(self, pattern_manager: PatternManager = None):
        self.pattern_manager = pattern_manager or PatternManager()
        self.exchange_analyzer = ExchangeAnalyzer()
        self.detected_patterns: List[PatternMatch] = []
        
        # Настройки фильтрации
        self.min_piece_relevance = 0.3      # Минимальная релевантность фигуры
        self.max_distance_from_action = 3   # Максимальное расстояние от места действия
        
    def detect_patterns_in_position(
        self,
        board: chess.Board,
        max_patterns: int = 5,
        include_exchanges: bool = True
    ) -> List[PatternMatch]:
        """Обнаружить паттерны в текущей позиции"""
        
        matches = []
        
        # 1. Найти совпадающие паттерны из базы
        stored_patterns = self.pattern_manager.find_matching_patterns(board, max_patterns * 2)
        
        for pattern, similarity in stored_patterns:
            match = self._analyze_pattern_match(board, pattern, similarity)
            if match and match.confidence > 0.4:
                matches.append(match)
        
        # 2. Динамическое обнаружение тактических паттернов
        tactical_matches = self._detect_tactical_patterns(board)
        matches.extend(tactical_matches)
        
        # 3. Анализ размена (если включен)
        if include_exchanges:
            exchange_matches = self._detect_exchange_patterns(board)
            matches.extend(exchange_matches)
        
        # Сортировать по уверенности и ограничить количество
        matches.sort(key=lambda m: m.confidence, reverse=True)
        
        # Сохранить обнаруженные паттерны
        self.detected_patterns = matches[:max_patterns]
        
        return self.detected_patterns
    
    def _analyze_pattern_match(
        self,
        board: chess.Board,
        pattern: ChessPatternEnhanced,
        base_similarity: float
    ) -> Optional[PatternMatch]:
        """Анализировать совпадение с паттерном"""
        
        try:
            # Определить релевантные фигуры
            relevant_pieces = self._find_relevant_pieces(board, pattern)
            
            # Отфильтровать неучаствующие фигуры
            filtered_pieces = self._filter_irrelevant_pieces(board, pattern, relevant_pieces)
            
            # Вычислить уверенность
            confidence = self._calculate_match_confidence(
                board, pattern, relevant_pieces, base_similarity
            )
            
            if confidence < 0.3:
                return None
            
            # Определить предлагаемый ход
            suggested_move = self._determine_suggested_move(board, pattern)
            
            # Создать объяснение
            explanation = self._generate_explanation(pattern, relevant_pieces)
            
            return PatternMatch(
                pattern=pattern,
                confidence=confidence,
                relevant_pieces=relevant_pieces,
                filtered_pieces=filtered_pieces,
                suggested_move=suggested_move,
                alternative_moves=pattern.alternative_moves.copy(),
                explanation=explanation
            )
            
        except Exception as e:
            logger.error(f"Error analyzing pattern match: {e}")
            return None
    
    def _find_relevant_pieces(
        self,
        board: chess.Board,
        pattern: ChessPatternEnhanced
    ) -> List[PatternPiece]:
        """Найти фигуры, релевантные для паттерна"""
        
        relevant_pieces = []
        
        # Анализировать участвующие фигуры из паттерна
        for pattern_piece in pattern.participating_pieces:
            try:
                square = chess.parse_square(pattern_piece.square)
                current_piece = board.piece_at(square)
                
                if current_piece:
                    # Проверить соответствие типа и цвета
                    expected_type = getattr(chess, pattern_piece.piece_type.upper())
                    expected_color = chess.WHITE if pattern_piece.color == "white" else chess.BLACK
                    
                    if (current_piece.piece_type == expected_type and 
                        current_piece.color == expected_color):
                        
                        # Создать копию с актуальной информацией
                        relevant_piece = PatternPiece(
                            square=pattern_piece.square,
                            piece_type=pattern_piece.piece_type,
                            color=pattern_piece.color,
                            role=pattern_piece.role,
                            importance=pattern_piece.importance
                        )
                        relevant_pieces.append(relevant_piece)
                
            except Exception as e:
                logger.debug(f"Error processing pattern piece: {e}")
                continue
        
        # Добавить дополнительные релевантные фигуры
        additional_pieces = self._find_additional_relevant_pieces(board, pattern, relevant_pieces)
        relevant_pieces.extend(additional_pieces)
        
        return relevant_pieces
    
    def _find_additional_relevant_pieces(
        self,
        board: chess.Board,
        pattern: ChessPatternEnhanced,
        existing_pieces: List[PatternPiece]
    ) -> List[PatternPiece]:
        """Найти дополнительные релевантные фигуры"""
        
        additional_pieces = []
        existing_squares = {piece.square for piece in existing_pieces}
        
        # Определить центр активности
        activity_center = self._find_activity_center(existing_pieces)
        
        if not activity_center:
            return additional_pieces
        
        # Найти фигуры в радиусе активности
        for square in chess.SQUARES:
            square_name = chess.square_name(square)
            
            if square_name in existing_squares:
                continue
            
            piece = board.piece_at(square)
            if not piece:
                continue
            
            # Проверить расстояние от центра активности
            distance = self._calculate_square_distance(square, activity_center)
            
            if distance <= self.max_distance_from_action:
                # Определить роль фигуры
                role = self._determine_piece_role(board, square, existing_pieces)
                
                if role:
                    importance = max(0.1, 1.0 - distance * 0.2)  # Важность убывает с расстоянием
                    
                    additional_piece = PatternPiece(
                        square=square_name,
                        piece_type=chess.piece_name(piece.piece_type).lower(),
                        color="white" if piece.color == chess.WHITE else "black",
                        role=role,
                        importance=importance
                    )
                    additional_pieces.append(additional_piece)
        
        return additional_pieces
    
    def _filter_irrelevant_pieces(
        self,
        board: chess.Board,
        pattern: ChessPatternEnhanced,
        relevant_pieces: List[PatternPiece]
    ) -> List[str]:
        """Отфильтровать фигуры, не участвующие в паттерне"""
        
        filtered_pieces = []
        relevant_squares = {piece.square for piece in relevant_pieces}
        
        # Добавить явно исключенные фигуры из паттерна
        filtered_pieces.extend(pattern.excluded_pieces)
        
        # Найти фигуры, которые не участвуют в паттерне
        for square in chess.SQUARES:
            square_name = chess.square_name(square)
            
            if square_name in relevant_squares:
                continue  # Эта фигура релевантна
            
            piece = board.piece_at(square)
            if not piece:
                continue
            
            # Проверить критерии исключения
            should_exclude = (
                self._is_piece_inactive(board, square, relevant_pieces) or
                self._is_piece_too_far(square, relevant_pieces) or
                self._is_piece_not_moved_recently(board, square)
            )
            
            if should_exclude:
                filtered_pieces.append(square_name)
        
        return filtered_pieces
    
    def _is_piece_inactive(
        self,
        board: chess.Board,
        square: chess.Square,
        relevant_pieces: List[PatternPiece]
    ) -> bool:
        """Проверить, неактивна ли фигура"""
        
        piece = board.piece_at(square)
        if not piece:
            return True
        
        # Фигура неактивна, если она не атакует и не защищает релевантные поля
        relevant_squares = [chess.parse_square(p.square) for p in relevant_pieces]
        
        attacks = board.attacks(square)
        
        # Проверить, атакует ли фигура релевантные поля
        for rel_square in relevant_squares:
            if rel_square in attacks:
                return False  # Фигура активна
        
        # Проверить, защищает ли фигура релевантные поля
        for rel_square in relevant_squares:
            defenders = board.attackers(piece.color, rel_square)
            if square in defenders:
                return False  # Фигура активна
        
        return True  # Фигура неактивна
    
    def _is_piece_too_far(
        self,
        square: chess.Square,
        relevant_pieces: List[PatternPiece]
    ) -> bool:
        """Проверить, слишком ли далеко фигура от действия"""
        
        if not relevant_pieces:
            return False
        
        # Найти минимальное расстояние до релевантных фигур
        min_distance = float('inf')
        
        for piece in relevant_pieces:
            try:
                piece_square = chess.parse_square(piece.square)
                distance = self._calculate_square_distance(square, piece_square)
                min_distance = min(min_distance, distance)
            except:
                continue
        
        return min_distance > self.max_distance_from_action
    
    def _is_piece_not_moved_recently(
        self,
        board: chess.Board,
        square: chess.Square
    ) -> bool:
        """Проверить, не двигалась ли фигура недавно"""
        
        # Проверить последние несколько ходов
        recent_moves = board.move_stack[-6:]  # Последние 3 полных хода
        
        for move in recent_moves:
            if move.from_square == square or move.to_square == square:
                return False  # Фигура двигалась недавно
        
        return True  # Фигура не двигалась
    
    def _detect_tactical_patterns(self, board: chess.Board) -> List[PatternMatch]:
        """Динамическое обнаружение тактических паттернов"""
        
        tactical_matches = []
        
        # Обнаружить вилки
        fork_matches = self._detect_forks(board)
        tactical_matches.extend(fork_matches)
        
        # Обнаружить связки
        pin_matches = self._detect_pins(board)
        tactical_matches.extend(pin_matches)
        
        # Обнаружить висячие фигуры
        hanging_matches = self._detect_hanging_pieces(board)
        tactical_matches.extend(hanging_matches)
        
        return tactical_matches
    
    def _detect_forks(self, board: chess.Board) -> List[PatternMatch]:
        """Обнаружить возможные вилки"""
        
        fork_matches = []
        
        for move in board.legal_moves:
            piece = board.piece_at(move.from_square)
            if not piece or piece.piece_type != chess.KNIGHT:
                continue
            
            # Симулировать ход
            test_board = board.copy()
            test_board.push(move)
            
            # Проверить, создает ли ход вилку
            attacks = test_board.attacks(move.to_square)
            valuable_targets = []
            
            for target_square in attacks:
                target_piece = test_board.piece_at(target_square)
                if (target_piece and 
                    target_piece.color != piece.color and
                    target_piece.piece_type in [chess.KING, chess.QUEEN, chess.ROOK]):
                    valuable_targets.append(target_square)
            
            if len(valuable_targets) >= 2:
                # Создать паттерн вилки
                fork_pattern = self._create_fork_pattern(board, move, valuable_targets)
                
                match = PatternMatch(
                    pattern=fork_pattern,
                    confidence=0.8,
                    relevant_pieces=fork_pattern.participating_pieces,
                    filtered_pieces=[],
                    suggested_move=move.uci(),
                    alternative_moves=[],
                    explanation=f"Конь создает вилку, атакуя {len(valuable_targets)} ценных фигур"
                )
                fork_matches.append(match)
        
        return fork_matches
    
    def _detect_pins(self, board: chess.Board) -> List[PatternMatch]:
        """Обнаружить возможные связки"""
        
        pin_matches = []
        
        for move in board.legal_moves:
            piece = board.piece_at(move.from_square)
            if not piece or piece.piece_type not in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
                continue
            
            # Симулировать ход
            test_board = board.copy()
            test_board.push(move)
            
            # Проверить, создает ли ход связку
            pin_info = self._check_for_pin(test_board, move.to_square, piece.color)
            
            if pin_info:
                pin_pattern = self._create_pin_pattern(board, move, pin_info)
                
                match = PatternMatch(
                    pattern=pin_pattern,
                    confidence=0.7,
                    relevant_pieces=pin_pattern.participating_pieces,
                    filtered_pieces=[],
                    suggested_move=move.uci(),
                    alternative_moves=[],
                    explanation=f"Создание связки: {pin_info['description']}"
                )
                pin_matches.append(match)
        
        return pin_matches
    
    def _detect_hanging_pieces(self, board: chess.Board) -> List[PatternMatch]:
        """Обнаружить висячие фигуры"""
        
        hanging_matches = []
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if not piece or piece.color == board.turn:
                continue
            
            # Проверить, висит ли фигура
            attackers = len(board.attackers(board.turn, square))
            defenders = len(board.attackers(not board.turn, square))
            
            if attackers > 0 and defenders == 0 and piece.piece_type != chess.PAWN:
                # Найти лучший ход для взятия
                capture_moves = [
                    move for move in board.legal_moves 
                    if move.to_square == square
                ]
                
                if capture_moves:
                    best_capture = min(
                        capture_moves,
                        key=lambda m: self.exchange_analyzer.piece_values[
                            board.piece_at(m.from_square).piece_type
                        ]
                    )
                    
                    hanging_pattern = self._create_hanging_pattern(board, square, piece)
                    
                    match = PatternMatch(
                        pattern=hanging_pattern,
                        confidence=0.9,
                        relevant_pieces=hanging_pattern.participating_pieces,
                        filtered_pieces=[],
                        suggested_move=best_capture.uci(),
                        alternative_moves=[m.uci() for m in capture_moves[1:]],
                        explanation=f"Висячая фигура: {chess.piece_name(piece.piece_type)}"
                    )
                    hanging_matches.append(match)
        
        return hanging_matches
    
    def _detect_exchange_patterns(self, board: chess.Board) -> List[PatternMatch]:
        """Обнаружить паттерны размена"""
        
        exchange_matches = []
        
        # Анализировать возможные размены
        exchanges = self.exchange_analyzer.analyze_exchange_patterns(board, depth=3)
        
        for exchange in exchanges:
            if abs(exchange.material_balance) >= 1:  # Значимый размен
                exchange_pattern = self._create_exchange_pattern(board, exchange)
                
                confidence = min(0.9, exchange.probability)
                if exchange.material_balance > 0:
                    confidence += 0.1  # Бонус за выгодный размен
                
                match = PatternMatch(
                    pattern=exchange_pattern,
                    confidence=confidence,
                    relevant_pieces=exchange_pattern.participating_pieces,
                    filtered_pieces=[],
                    suggested_move=exchange.moves[0],
                    alternative_moves=exchange.moves[1:],
                    explanation=f"Размен с балансом {exchange.material_balance} пешек"
                )
                exchange_matches.append(match)
        
        return exchange_matches
    
    # Вспомогательные методы для создания паттернов
    
    def _create_fork_pattern(
        self,
        board: chess.Board,
        move: chess.Move,
        targets: List[chess.Square]
    ) -> ChessPatternEnhanced:
        """Создать паттерн вилки"""
        
        participating_pieces = []
        
        # Добавить атакующего коня
        knight_square = chess.square_name(move.to_square)
        participating_pieces.append(PatternPiece(
            square=knight_square,
            piece_type="knight",
            color="white" if board.turn == chess.WHITE else "black",
            role="attacker",
            importance=1.0
        ))
        
        # Добавить цели
        for i, target_square in enumerate(targets):
            target_piece = board.piece_at(target_square)
            if target_piece:
                participating_pieces.append(PatternPiece(
                    square=chess.square_name(target_square),
                    piece_type=chess.piece_name(target_piece.piece_type).lower(),
                    color="white" if target_piece.color == chess.WHITE else "black",
                    role="target",
                    importance=0.9 - i * 0.1
                ))
        
        return ChessPatternEnhanced(
            id=f"fork_{move.uci()}_{hash(board.fen()) % 10000}",
            name="Динамическая вилка",
            description="Обнаруженная вилка конём",
            category=PatternCategory.TACTICAL,
            fen=board.fen(),
            key_move=move.uci(),
            participating_pieces=participating_pieces,
            frequency=0.3,
            success_rate=0.8,
            game_phase=self.pattern_manager._determine_game_phase(board),
            tags=["fork", "knight", "dynamic"]
        )
    
    def _create_pin_pattern(
        self,
        board: chess.Board,
        move: chess.Move,
        pin_info: Dict[str, Any]
    ) -> ChessPatternEnhanced:
        """Создать паттерн связки"""
        
        participating_pieces = []
        
        # Добавить связывающую фигуру
        attacker_piece = board.piece_at(move.from_square)
        participating_pieces.append(PatternPiece(
            square=chess.square_name(move.to_square),
            piece_type=chess.piece_name(attacker_piece.piece_type).lower(),
            color="white" if attacker_piece.color == chess.WHITE else "black",
            role="attacker",
            importance=1.0
        ))
        
        # Добавить связанную фигуру и цель
        if "pinned_square" in pin_info:
            pinned_piece = board.piece_at(pin_info["pinned_square"])
            if pinned_piece:
                participating_pieces.append(PatternPiece(
                    square=chess.square_name(pin_info["pinned_square"]),
                    piece_type=chess.piece_name(pinned_piece.piece_type).lower(),
                    color="white" if pinned_piece.color == chess.WHITE else "black",
                    role="target",
                    importance=0.8
                ))
        
        return ChessPatternEnhanced(
            id=f"pin_{move.uci()}_{hash(board.fen()) % 10000}",
            name="Динамическая связка",
            description="Обнаруженная связка",
            category=PatternCategory.TACTICAL,
            fen=board.fen(),
            key_move=move.uci(),
            participating_pieces=participating_pieces,
            frequency=0.25,
            success_rate=0.7,
            game_phase=self.pattern_manager._determine_game_phase(board),
            tags=["pin", "dynamic"]
        )
    
    def _create_hanging_pattern(
        self,
        board: chess.Board,
        square: chess.Square,
        piece: chess.Piece
    ) -> ChessPatternEnhanced:
        """Создать паттерн висячей фигуры"""
        
        participating_pieces = [
            PatternPiece(
                square=chess.square_name(square),
                piece_type=chess.piece_name(piece.piece_type).lower(),
                color="white" if piece.color == chess.WHITE else "black",
                role="target",
                importance=1.0
            )
        ]
        
        return ChessPatternEnhanced(
            id=f"hanging_{chess.square_name(square)}_{hash(board.fen()) % 10000}",
            name="Висячая фигура",
            description="Обнаруженная висячая фигура",
            category=PatternCategory.TACTICAL,
            fen=board.fen(),
            key_move="",  # Будет определен в match
            participating_pieces=participating_pieces,
            frequency=0.4,
            success_rate=0.9,
            game_phase=self.pattern_manager._determine_game_phase(board),
            tags=["hanging", "dynamic"]
        )
    
    def _create_exchange_pattern(
        self,
        board: chess.Board,
        exchange: ExchangeSequence
    ) -> ChessPatternEnhanced:
        """Создать паттерн размена"""
        
        # Определить тип размена
        if exchange.material_balance > 1:
            exchange_type = ExchangeType.FAVORABLE_TRADE
        elif exchange.material_balance < -1:
            exchange_type = ExchangeType.SACRIFICE
        else:
            exchange_type = ExchangeType.EQUAL_TRADE
        
        return ChessPatternEnhanced(
            id=f"exchange_{exchange.moves[0]}_{hash(board.fen()) % 10000}",
            name="Динамический размен",
            description=f"Размен с балансом {exchange.material_balance}",
            category=PatternCategory.EXCHANGE,
            fen=board.fen(),
            key_move=exchange.moves[0],
            alternative_moves=exchange.moves[1:],
            exchange_sequence=exchange,
            exchange_type=exchange_type,
            participating_pieces=[],  # Будет заполнено при анализе
            frequency=0.3,
            success_rate=exchange.probability,
            game_phase=self.pattern_manager._determine_game_phase(board),
            tags=["exchange", "dynamic"]
        )
    
    # Вспомогательные методы
    
    def _find_activity_center(self, pieces: List[PatternPiece]) -> Optional[chess.Square]:
        """Найти центр активности"""
        if not pieces:
            return None
        
        try:
            squares = [chess.parse_square(piece.square) for piece in pieces]
            
            # Вычислить средние координаты
            avg_file = sum(chess.square_file(sq) for sq in squares) / len(squares)
            avg_rank = sum(chess.square_rank(sq) for sq in squares) / len(squares)
            
            # Найти ближайшее поле
            center_square = chess.square(int(avg_file), int(avg_rank))
            return center_square
            
        except:
            return chess.E4  # Fallback
    
    def _calculate_square_distance(self, sq1: chess.Square, sq2: chess.Square) -> int:
        """Вычислить расстояние между полями"""
        file1, rank1 = chess.square_file(sq1), chess.square_rank(sq1)
        file2, rank2 = chess.square_file(sq2), chess.square_rank(sq2)
        
        return max(abs(file1 - file2), abs(rank1 - rank2))
    
    def _determine_piece_role(
        self,
        board: chess.Board,
        square: chess.Square,
        existing_pieces: List[PatternPiece]
    ) -> Optional[str]:
        """Определить роль фигуры в паттерне"""
        
        piece = board.piece_at(square)
        if not piece:
            return None
        
        # Проверить, атакует ли фигура существующие фигуры
        attacks = board.attacks(square)
        existing_squares = [chess.parse_square(p.square) for p in existing_pieces]
        
        for existing_square in existing_squares:
            if existing_square in attacks:
                existing_piece = board.piece_at(existing_square)
                if existing_piece and existing_piece.color != piece.color:
                    return "attacker"
                elif existing_piece and existing_piece.color == piece.color:
                    return "support"
        
        # Проверить, защищает ли фигура существующие фигуры
        for existing_square in existing_squares:
            defenders = board.attackers(piece.color, existing_square)
            if square in defenders:
                return "defender"
        
        return "observer"  # Фигура наблюдает за ситуацией
    
    def _calculate_match_confidence(
        self,
        board: chess.Board,
        pattern: ChessPatternEnhanced,
        relevant_pieces: List[PatternPiece],
        base_similarity: float
    ) -> float:
        """Вычислить уверенность в совпадении"""
        
        confidence = base_similarity
        
        # Бонус за количество совпадающих фигур
        expected_pieces = len(pattern.participating_pieces)
        actual_pieces = len(relevant_pieces)
        
        if expected_pieces > 0:
            piece_ratio = actual_pieces / expected_pieces
            confidence *= min(1.0, piece_ratio + 0.2)
        
        # Бонус за фазу игры
        current_phase = self.pattern_manager._determine_game_phase(board)
        if pattern.game_phase == current_phase or pattern.game_phase == "any":
            confidence += 0.1
        
        # Штраф за слишком много отфильтрованных фигур
        total_pieces = len(list(board.piece_map()))
        if total_pieces > 0:
            filter_ratio = len(pattern.excluded_pieces) / total_pieces
            confidence *= (1.0 - filter_ratio * 0.3)
        
        return min(1.0, confidence)
    
    def _determine_suggested_move(
        self,
        board: chess.Board,
        pattern: ChessPatternEnhanced
    ) -> str:
        """Определить предлагаемый ход"""
        
        # Проверить, является ли ключевой ход легальным
        try:
            move = chess.Move.from_uci(pattern.key_move)
            if move in board.legal_moves:
                return pattern.key_move
        except:
            pass
        
        # Попробовать альтернативные ходы
        for alt_move in pattern.alternative_moves:
            try:
                move = chess.Move.from_uci(alt_move)
                if move in board.legal_moves:
                    return alt_move
            except:
                continue
        
        # Если ничего не подходит, вернуть пустую строку
        return ""
    
    def _generate_explanation(
        self,
        pattern: ChessPatternEnhanced,
        relevant_pieces: List[PatternPiece]
    ) -> str:
        """Сгенерировать объяснение паттерна"""
        
        explanation_parts = [pattern.description]
        
        # Добавить информацию о участвующих фигурах
        attackers = [p for p in relevant_pieces if p.role == "attacker"]
        targets = [p for p in relevant_pieces if p.role == "target"]
        
        if attackers:
            attacker_names = [f"{p.piece_type} на {p.square}" for p in attackers]
            explanation_parts.append(f"Атакующие: {', '.join(attacker_names)}")
        
        if targets:
            target_names = [f"{p.piece_type} на {p.square}" for p in targets]
            explanation_parts.append(f"Цели: {', '.join(target_names)}")
        
        # Добавить информацию о размене
        if pattern.exchange_sequence:
            explanation_parts.append(
                f"Размен: {' -> '.join(pattern.exchange_sequence.moves)}"
            )
        
        return ". ".join(explanation_parts)
    
    def _check_for_pin(
        self,
        board: chess.Board,
        attacker_square: chess.Square,
        attacker_color: chess.Color
    ) -> Optional[Dict[str, Any]]:
        """Проверить, создает ли фигура связку"""
        
        piece = board.piece_at(attacker_square)
        if not piece or piece.piece_type not in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
            return None
        
        # Найти короля противника
        enemy_king_square = board.king(not attacker_color)
        if enemy_king_square is None:
            return None
        
        # Проверить, находятся ли атакующая фигура и король на одной линии
        try:
            between_squares = list(chess.between(attacker_square, enemy_king_square))
            
            if len(between_squares) == 1:
                pinned_square = between_squares[0]
                pinned_piece = board.piece_at(pinned_square)
                
                if pinned_piece and pinned_piece.color != attacker_color:
                    return {
                        "pinned_square": pinned_square,
                        "king_square": enemy_king_square,
                        "description": f"{chess.piece_name(pinned_piece.piece_type)} связана с королем"
                    }
        except:
            pass
        
        return None
