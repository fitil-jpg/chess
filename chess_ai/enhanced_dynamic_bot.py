"""
Enhanced Dynamic Bot

Улучшенная версия DynamicBot с интеграцией системы паттернов
для победы над Stockfish.
"""

from __future__ import annotations
import chess
import logging
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
import random
import math

from .dynamic_bot import DynamicBot
from .stockfish_bot import StockfishBot
from chess_ai.enhanced_pattern_system import PatternManager
from chess_ai.enhanced_pattern_detector import EnhancedPatternDetector, PatternMatch
from core.evaluator import Evaluator
from utils import GameContext

logger = logging.getLogger(__name__)


class EnhancedDynamicBot(DynamicBot):
    """
    Улучшенная версия DynamicBot с интеграцией паттернов и
    специальными стратегиями против Stockfish.
    """
    
    def __init__(
        self,
        color: bool,
        *,
        weights: Dict[str, float] = None,
        use_patterns: bool = True,
        anti_stockfish_mode: bool = True,
        pattern_weight: float = 2.0,
        **kwargs
    ):
        # Инициализировать базовый DynamicBot с оптимизированными весами
        optimized_weights = self._get_optimized_weights()
        if weights:
            optimized_weights.update(weights)
        
        super().__init__(color, weights=optimized_weights, **kwargs)
        
        # Система паттернов
        self.use_patterns = use_patterns
        self.pattern_manager = PatternManager() if use_patterns else None
        self.pattern_detector = EnhancedPatternDetector(self.pattern_manager) if use_patterns else None
        self.pattern_weight = pattern_weight
        
        # Анти-Stockfish режим
        self.anti_stockfish_mode = anti_stockfish_mode
        self.opponent_type = "unknown"
        self.move_history = []
        self.position_history = []
        
        # Адаптивные стратегии
        self.adaptive_weights = optimized_weights.copy()
        self.performance_history = defaultdict(list)
        self.learning_rate = 0.1
        
        # Книга дебютов против Stockfish
        self.anti_stockfish_book = self._create_anti_stockfish_book()
        
        # Эндшпильные таблицы
        self.endgame_knowledge = self._load_endgame_knowledge()
        
        logger.info(f"Enhanced DynamicBot initialized for {'white' if color else 'black'}")
    
    def choose_move(
        self,
        board: chess.Board,
        context: GameContext = None,
        evaluator: Evaluator = None,
        debug: bool = False
    ) -> Tuple[Optional[chess.Move], float]:
        """Выбрать ход с использованием улучшенной логики"""
        
        # Обновить историю
        self._update_history(board)
        
        # Определить тип противника
        self._analyze_opponent(board)
        
        # 1. Проверить дебютную книгу против Stockfish
        if self.anti_stockfish_mode and self.opponent_type == "stockfish":
            book_move = self._get_anti_stockfish_book_move(board)
            if book_move:
                return book_move, 0.9
        
        # 2. Использовать паттерны
        pattern_move, pattern_confidence = self._get_pattern_move(board)
        
        # 3. Получить ходы от базового DynamicBot
        base_move, base_confidence = super().choose_move(board, context, evaluator, debug)
        
        # 4. Специальные анти-Stockfish стратегии
        anti_sf_move, anti_sf_confidence = self._get_anti_stockfish_move(board)
        
        # 5. Эндшпильная экспертиза
        endgame_move, endgame_confidence = self._get_endgame_move(board)
        
        # Объединить все предложения
        candidates = []
        
        if pattern_move:
            candidates.append((pattern_move, pattern_confidence * self.pattern_weight, "pattern"))
        
        if base_move:
            candidates.append((base_move, base_confidence, "dynamic"))
        
        if anti_sf_move:
            candidates.append((anti_sf_move, anti_sf_confidence * 1.5, "anti_stockfish"))
        
        if endgame_move:
            candidates.append((endgame_move, endgame_confidence * 1.3, "endgame"))
        
        # Выбрать лучший ход
        if candidates:
            # Сортировать по уверенности
            candidates.sort(key=lambda x: x[1], reverse=True)
            
            # Добавить случайность для непредсказуемости против Stockfish
            if self.anti_stockfish_mode and len(candidates) > 1:
                top_candidates = [c for c in candidates if c[1] >= candidates[0][1] * 0.8]
                if len(top_candidates) > 1:
                    chosen = random.choice(top_candidates)
                else:
                    chosen = candidates[0]
            else:
                chosen = candidates[0]
            
            move, confidence, source = chosen
            
            if debug:
                logger.info(f"Enhanced move selection: {move} (confidence: {confidence:.3f}, source: {source})")
                for i, (m, c, s) in enumerate(candidates[:3]):
                    logger.info(f"  {i+1}. {m} ({c:.3f}, {s})")
            
            return move, confidence
        
        # Fallback к базовому DynamicBot
        return super().choose_move(board, context, evaluator, debug)
    
    def _get_optimized_weights(self) -> Dict[str, float]:
        """Получить оптимизированные веса для ботов"""
        return {
            "AggressiveBot": 1.2,      # Повышенная агрессия против Stockfish
            "EndgameBot": 1.5,         # Сильный эндшпиль
            "FortifyBot": 0.8,         # Меньше защиты, больше атаки
            "CriticalBot": 1.3,        # Важно находить критические моменты
            "NeuralBot": 1.1,          # Нейросеть как дополнение
            "RandomBot": 0.3,          # Минимальная случайность
        }
    
    def _get_pattern_move(self, board: chess.Board) -> Tuple[Optional[chess.Move], float]:
        """Получить ход на основе паттернов"""
        if not self.use_patterns or not self.pattern_detector:
            return None, 0.0
        
        try:
            matches = self.pattern_detector.detect_patterns_in_position(
                board, max_patterns=5, include_exchanges=True
            )
            
            if not matches:
                return None, 0.0
            
            # Выбрать лучший паттерн
            best_match = max(matches, key=lambda m: m.confidence)
            
            if best_match.suggested_move and best_match.confidence > 0.5:
                try:
                    move = chess.Move.from_uci(best_match.suggested_move)
                    if move in board.legal_moves:
                        return move, best_match.confidence
                except:
                    pass
            
            return None, 0.0
            
        except Exception as e:
            logger.error(f"Error in pattern move selection: {e}")
            return None, 0.0
    
    def _get_anti_stockfish_move(self, board: chess.Board) -> Tuple[Optional[chess.Move], float]:
        """Получить ход, специально направленный против Stockfish"""
        if not self.anti_stockfish_mode or self.opponent_type != "stockfish":
            return None, 0.0
        
        # Стратегии против Stockfish:
        
        # 1. Избегать симметричных позиций
        asymmetry_move = self._find_asymmetric_move(board)
        if asymmetry_move:
            return asymmetry_move, 0.7
        
        # 2. Создавать сложные тактические позиции
        tactical_move = self._find_tactical_complexity_move(board)
        if tactical_move:
            return tactical_move, 0.6
        
        # 3. Жертвы и гамбиты для усложнения
        sacrifice_move = self._find_sacrifice_move(board)
        if sacrifice_move:
            return sacrifice_move, 0.5
        
        return None, 0.0
    
    def _get_endgame_move(self, board: chess.Board) -> Tuple[Optional[chess.Move], float]:
        """Получить эндшпильный ход"""
        if not self._is_endgame(board):
            return None, 0.0
        
        # Использовать эндшпильные знания
        for pattern, moves in self.endgame_knowledge.items():
            if self._matches_endgame_pattern(board, pattern):
                for move_uci in moves:
                    try:
                        move = chess.Move.from_uci(move_uci)
                        if move in board.legal_moves:
                            return move, 0.8
                    except:
                        continue
        
        return None, 0.0
    
    def _get_anti_stockfish_book_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Получить ход из дебютной книги против Stockfish"""
        fen_key = board.fen().split()[0]  # Только расстановка фигур
        
        if fen_key in self.anti_stockfish_book:
            moves = self.anti_stockfish_book[fen_key]
            for move_uci in moves:
                try:
                    move = chess.Move.from_uci(move_uci)
                    if move in board.legal_moves:
                        return move
                except:
                    continue
        
        return None
    
    def _create_anti_stockfish_book(self) -> Dict[str, List[str]]:
        """Создать дебютную книгу против Stockfish"""
        return {
            # Начальная позиция - избегать главных линий
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR": ["b3", "f3", "h3", "a3"],
            
            # Против e4 - играть необычные защиты
            "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR": ["a6", "h6", "f6", "b6"],
            
            # Против d4 - избегать стандартных ответов
            "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR": ["e6", "g6", "b6", "f5"],
            
            # Сицилианская защита - необычные варианты
            "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR": ["f4", "Bc4", "d3"],
        }
    
    def _load_endgame_knowledge(self) -> Dict[str, List[str]]:
        """Загрузить эндшпильные знания"""
        return {
            # Король + пешка против короля
            "KP_vs_K": ["Kf5", "Ke5", "Kd5", "Kc5"],
            
            # Ладейный эндшпиль
            "R_vs_R": ["Ra1", "Rb1", "Rc1", "Rd1"],
            
            # Ферзь против пешек
            "Q_vs_P": ["Qh5+", "Qg5+", "Qf5+", "Qe5+"],
        }
    
    def _update_history(self, board: chess.Board):
        """Обновить историю ходов и позиций"""
        current_fen = board.fen()
        
        if len(self.position_history) == 0 or self.position_history[-1] != current_fen:
            self.position_history.append(current_fen)
            
            if len(board.move_stack) > len(self.move_history):
                self.move_history.extend(board.move_stack[len(self.move_history):])
        
        # Ограничить размер истории
        if len(self.position_history) > 100:
            self.position_history = self.position_history[-50:]
        if len(self.move_history) > 100:
            self.move_history = self.move_history[-50:]
    
    def _analyze_opponent(self, board: chess.Board):
        """Анализировать тип противника"""
        if len(self.move_history) < 4:
            return
        
        # Простая эвристика для определения Stockfish
        # Stockfish часто играет очень точно и предпочитает центр
        recent_moves = self.move_history[-4:]
        
        stockfish_indicators = 0
        for move in recent_moves:
            # Ходы в центр
            if move.to_square in [chess.E4, chess.D4, chess.E5, chess.D5]:
                stockfish_indicators += 1
            
            # Развитие фигур
            piece = board.piece_at(move.to_square)
            if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
                stockfish_indicators += 1
        
        if stockfish_indicators >= 3:
            self.opponent_type = "stockfish"
        else:
            self.opponent_type = "human"
    
    def _find_asymmetric_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Найти ход, создающий асимметрию"""
        for move in board.legal_moves:
            # Предпочитать ходы на фланги
            if chess.square_file(move.to_square) in [0, 1, 6, 7]:  # a, b, g, h файлы
                return move
            
            # Предпочитать необычные ходы пешками
            piece = board.piece_at(move.from_square)
            if piece and piece.piece_type == chess.PAWN:
                if chess.square_file(move.to_square) in [0, 2, 5, 7]:  # a, c, f, h файлы
                    return move
        
        return None
    
    def _find_tactical_complexity_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Найти ход, создающий тактическую сложность"""
        complex_moves = []
        
        for move in board.legal_moves:
            complexity_score = 0
            
            # Жертвы повышают сложность
            if board.is_capture(move):
                captured = board.piece_at(move.to_square)
                moving = board.piece_at(move.from_square)
                if captured and moving:
                    # Жертва более ценной фигуры
                    piece_values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, 
                                  chess.ROOK: 5, chess.QUEEN: 9}
                    if piece_values.get(moving.piece_type, 0) > piece_values.get(captured.piece_type, 0):
                        complexity_score += 2
            
            # Шахи повышают сложность
            test_board = board.copy()
            test_board.push(move)
            if test_board.is_check():
                complexity_score += 1
            
            # Атаки на короля
            enemy_king = test_board.king(not board.turn)
            if enemy_king and test_board.is_attacked_by(board.turn, enemy_king):
                complexity_score += 1
            
            if complexity_score > 0:
                complex_moves.append((move, complexity_score))
        
        if complex_moves:
            # Выбрать самый сложный ход
            complex_moves.sort(key=lambda x: x[1], reverse=True)
            return complex_moves[0][0]
        
        return None
    
    def _find_sacrifice_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Найти жертву для усложнения позиции"""
        piece_values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, 
                       chess.ROOK: 5, chess.QUEEN: 9}
        
        for move in board.legal_moves:
            if not board.is_capture(move):
                continue
            
            captured = board.piece_at(move.to_square)
            moving = board.piece_at(move.from_square)
            
            if not captured or not moving:
                continue
            
            # Жертва фигуры за пешку или меньшую фигуру
            moving_value = piece_values.get(moving.piece_type, 0)
            captured_value = piece_values.get(captured.piece_type, 0)
            
            if moving_value > captured_value and moving_value >= 3:  # Жертва минимум легкой фигуры
                # Проверить, дает ли жертва компенсацию
                test_board = board.copy()
                test_board.push(move)
                
                # Простая проверка: создает ли атаку на короля
                enemy_king = test_board.king(not board.turn)
                if enemy_king and test_board.is_attacked_by(board.turn, enemy_king):
                    return move
        
        return None
    
    def _is_endgame(self, board: chess.Board) -> bool:
        """Проверить, является ли позиция эндшпилем"""
        # Подсчитать материал
        piece_count = 0
        for piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]:
            piece_count += len(board.pieces(piece_type, chess.WHITE))
            piece_count += len(board.pieces(piece_type, chess.BLACK))
        
        return piece_count <= 6  # Эндшпиль при <= 6 фигур (без пешек и королей)
    
    def _matches_endgame_pattern(self, board: chess.Board, pattern: str) -> bool:
        """Проверить, соответствует ли позиция эндшпильному паттерну"""
        # Упрощенная проверка паттернов
        if pattern == "KP_vs_K":
            # Король + пешка против короля
            white_pieces = sum(len(board.pieces(pt, chess.WHITE)) for pt in chess.PIECE_TYPES)
            black_pieces = sum(len(board.pieces(pt, chess.BLACK)) for pt in chess.PIECE_TYPES)
            return (white_pieces == 2 and black_pieces == 1) or (white_pieces == 1 and black_pieces == 2)
        
        elif pattern == "R_vs_R":
            # Ладья против ладьи
            return (len(board.pieces(chess.ROOK, chess.WHITE)) == 1 and 
                   len(board.pieces(chess.ROOK, chess.BLACK)) == 1 and
                   sum(len(board.pieces(pt, chess.WHITE)) for pt in chess.PIECE_TYPES) <= 3 and
                   sum(len(board.pieces(pt, chess.BLACK)) for pt in chess.PIECE_TYPES) <= 3)
        
        elif pattern == "Q_vs_P":
            # Ферзь против пешек
            return (len(board.pieces(chess.QUEEN, chess.WHITE)) + len(board.pieces(chess.QUEEN, chess.BLACK)) == 1)
        
        return False
    
    def get_last_reason(self) -> str:
        """Получить причину последнего хода"""
        return "Enhanced Dynamic Bot with Pattern Recognition"
    
    def get_last_features(self) -> Dict[str, Any]:
        """Получить характеристики последнего хода"""
        return {
            "use_patterns": self.use_patterns,
            "anti_stockfish_mode": self.anti_stockfish_mode,
            "opponent_type": self.opponent_type,
            "pattern_weight": self.pattern_weight,
            "move_count": len(self.move_history)
        }
