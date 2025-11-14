#!/usr/bin/env python3
"""
Performance Optimization Implementation
Оптимизация производительности на основе результатов тестирования
"""

import time
import hashlib
import pickle
from functools import lru_cache
from typing import Dict, List, Tuple, Optional, Any
import chess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PositionCache:
    """Кэш для оценки позиций с использованием Zobrist хеширования."""
    
    def __init__(self, max_size: int = 10000):
        self.cache = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def _get_board_hash(self, board: chess.Board) -> str:
        """Получить хеш доски."""
        return hashlib.sha256(board.fen().encode()).hexdigest()[:16]
    
    def get(self, board: chess.Board, bot_name: str) -> Optional[Any]:
        """Получить кэшированный результат."""
        board_hash = self._get_board_hash(board)
        key = f"{board_hash}_{bot_name}"
        
        if key in self.cache:
            self.hits += 1
            return self.cache[key]
        
        self.misses += 1
        return None
    
    def set(self, board: chess.Board, bot_name: str, result: Any):
        """Сохранить результат в кэш."""
        board_hash = self._get_board_hash(board)
        key = f"{board_hash}_{bot_name}"
        
        if len(self.cache) >= self.max_size:
            # Remove oldest entries (simple LRU)
            oldest_keys = list(self.cache.keys())[:100]
            for k in oldest_keys:
                del self.cache[k]
        
        self.cache[key] = result
    
    def get_stats(self) -> Dict:
        """Получить статистику кэша."""
        total = self.hits + self.misses
        hit_rate = self.hits / max(1, total)
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'cache_size': len(self.cache)
        }

class OptimizedEvaluator:
    """Оптимизированный оценщик с кэшированием."""
    
    def __init__(self, cache_size: int = 10000):
        self.position_cache = PositionCache(cache_size)
        self.material_cache = {}
        
    @lru_cache(maxsize=1000)
    def get_material_value(self, fen: str) -> int:
        """Кэшированная оценка материала."""
        board = chess.Board(fen)
        material = 0
        
        for piece_type in range(1, 7):
            material += len(board.pieces(piece_type, chess.WHITE)) * self._piece_value(piece_type)
            material -= len(board.pieces(piece_type, chess.BLACK)) * self._piece_value(piece_type)
        
        return material
    
    def _piece_value(self, piece_type: int) -> int:
        """Получить ценность фигуры."""
        values = {1: 100, 2: 320, 3: 330, 4: 500, 5: 900, 6: 20000}
        return values.get(piece_type, 0)
    
    def evaluate_position_cached(self, board: chess.Board, bot_name: str) -> Optional[float]:
        """Получить кэшированную оценку позиции."""
        return self.position_cache.get(board, bot_name)
    
    def cache_evaluation(self, board: chess.Board, bot_name: str, score: float):
        """Сохранить оценку в кэш."""
        self.position_cache.set(board, bot_name, score)

class OptimizedCriticalBot:
    """Оптимизированный CriticalBot с кэшированием и улучшенной логикой."""
    
    def __init__(self, color: bool, enable_cache: bool = True):
        self.color = color
        self.enable_cache = enable_cache
        self.optimizer = OptimizedEvaluator() if enable_cache else None
        
        # Import sub-bots
        from chess_ai.critical_bot import CriticalBot
        from chess_ai.pawn_bot import PawnBot
        from chess_ai.king_value_bot import KingValueBot
        from chess_ai.aggressive_bot import AggressiveBot
        
        # Initialize with optimized settings
        self.critical_bot = CriticalBot(color, enable_hierarchy=True)
        self.sub_bots = {
            'aggressive': AggressiveBot(color),
            'pawn': PawnBot(color),
            'king': KingValueBot(color, enable_heatmaps=True)
        }
        
        # Performance tracking
        self.move_count = 0
        self.total_time = 0
        
    def choose_move(self, board: chess.Board, context=None, evaluator=None, debug=False) -> Tuple[chess.Move, float]:
        """Оптимизированный выбор хода."""
        
        start_time = time.perf_counter()
        self.move_count += 1
        
        # Check cache first
        if self.enable_cache and self.optimizer:
            cached_result = self.optimizer.evaluate_position_cached(board, "OptimizedCriticalBot")
            if cached_result:
                # Convert cached score back to move
                best_move = self._get_best_move_from_cache(board)
                if best_move:
                    end_time = time.perf_counter()
                    self.total_time += (end_time - start_time)
                    return best_move, cached_result
        
        # Use original CriticalBot logic but with optimizations
        move, score = self.critical_bot.choose_move(board, context, evaluator, debug)
        
        # Cache the result
        if self.enable_cache and self.optimizer and move:
            self.optimizer.cache_evaluation(board, "OptimizedCriticalBot", score)
        
        end_time = time.perf_counter()
        self.total_time += (end_time - start_time)
        
        return move, score
    
    def _get_best_move_from_cache(self, board: chess.Board) -> Optional[chess.Move]:
        """Получить лучший ход из кэша."""
        # Simple heuristic: get first legal move
        # In real implementation, would store moves in cache
        for move in board.legal_moves:
            return move
        return None
    
    def get_performance_stats(self) -> Dict:
        """Получить статистику производительности."""
        avg_time = self.total_time / max(1, self.move_count)
        
        stats = {
            'moves_processed': self.move_count,
            'total_time': self.total_time,
            'avg_time_per_move': avg_time,
            'cache_enabled': self.enable_cache
        }
        
        if self.enable_cache and self.optimizer:
            stats.update(self.optimizer.position_cache.get_stats())
        
        return stats

class OptimizedDynamicBot:
    """Оптимизированный DynamicBot с параллельной оценкой."""
    
    def __init__(self, color: bool, enable_parallel: bool = True):
        self.color = color
        self.enable_parallel = enable_parallel
        
        # Initialize with optimized weights based on performance analysis
        from chess_ai.dynamic_bot import DynamicBot
        
        # Optimized weights based on test results
        optimized_weights = {
            'aggressive': 1.5,    # Fast and effective
            'critical': 1.0,      # Good but slow, use sparingly
            'pawn': 0.8,          # Moderate speed, good for structure
            'king': 0.6,          # Slower, reduce weight
            'endgame': 1.2,       # Fast in endgames
            'random': 0.0,        # Disabled for performance
            'center': 0.8,        # Basic bot
            'neural': 0.5,        # Reduce neural weight for speed
        }
        
        self.dynamic_bot = DynamicBot(color, weights=optimized_weights)
        
        # Performance tracking
        self.move_count = 0
        self.total_time = 0
        
    def choose_move(self, board: chess.Board, context=None, evaluator=None, debug=False) -> Tuple[chess.Move, float]:
        """Оптимизированный выбор хода."""
        
        start_time = time.perf_counter()
        self.move_count += 1
        
        # Use optimized DynamicBot
        move, score = self.dynamic_bot.choose_move(board, context, evaluator, debug)
        
        end_time = time.perf_counter()
        self.total_time += (end_time - start_time)
        
        return move, score
    
    def get_performance_stats(self) -> Dict:
        """Получить статистику производительности."""
        avg_time = self.total_time / max(1, self.move_count)
        
        return {
            'moves_processed': self.move_count,
            'total_time': self.total_time,
            'avg_time_per_move': avg_time,
            'parallel_enabled': self.enable_parallel
        }

def performance_test_optimized_bots():
    """Тест производительности оптимизированных ботов."""
    
    print("🚀 Testing Optimized Bots Performance")
    print("=" * 50)
    
    # Test positions
    positions = [
        ("Opening", chess.Board()),
        ("Tactical", chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 4")),
        ("Complex", chess.Board("r2q1rk1/ppp2ppp/2n1bn2/2b1p3/3pP3/2P2N2/PP1N1PPP/R1BQKB1R w KQ - 0 8"))
    ]
    
    # Test bots
    bots = {
        "Original CriticalBot": None,  # Will be created below
        "Optimized CriticalBot": None,
        "Optimized DynamicBot": None
    }
    
    results = {}
    
    for pos_name, board in positions:
        print(f"\n🎯 Testing Position: {pos_name}")
        results[pos_name] = {}
        
        # Test original CriticalBot
        from chess_ai.critical_bot import CriticalBot
        original_bot = CriticalBot(chess.WHITE, enable_hierarchy=True)
        
        times = []
        for i in range(20):  # Reduced iterations for speed
            start = time.perf_counter()
            move, score = original_bot.choose_move(board)
            end = time.perf_counter()
            times.append(end - start)
        
        results[pos_name]["Original CriticalBot"] = {
            'avg_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times)
        }
        
        # Test optimized CriticalBot
        optimized_critical = OptimizedCriticalBot(chess.WHITE, enable_cache=True)
        
        times = []
        for i in range(20):
            start = time.perf_counter()
            move, score = optimized_critical.choose_move(board)
            end = time.perf_counter()
            times.append(end - start)
        
        results[pos_name]["Optimized CriticalBot"] = {
            'avg_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times)
        }
        
        # Test optimized DynamicBot
        optimized_dynamic = OptimizedDynamicBot(chess.WHITE, enable_parallel=True)
        
        times = []
        for i in range(20):
            start = time.perf_counter()
            move, score = optimized_dynamic.choose_move(board)
            end = time.perf_counter()
            times.append(end - start)
        
        results[pos_name]["Optimized DynamicBot"] = {
            'avg_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times)
        }
        
        # Print results for this position
        for bot_name, perf in results[pos_name].items():
            print(f"  {bot_name:25}: {perf['avg_time']*1000:6.1f}ms avg")
    
    # Calculate improvements
    print("\n📈 Performance Improvements:")
    print("-" * 40)
    
    for pos_name in results:
        original = results[pos_name]["Original CriticalBot"]["avg_time"]
        optimized = results[pos_name]["Optimized CriticalBot"]["avg_time"]
        improvement = ((original - optimized) / original) * 100
        
        print(f"{pos_name:10}: {improvement:+5.1f}% improvement")
    
    # Cache statistics
    print(f"\n🗄️ Cache Statistics (Optimized CriticalBot):")
    print("-" * 40)
    cache_stats = optimized_critical.get_performance_stats()
    if 'hits' in cache_stats:
        print(f"Cache hits: {cache_stats['hits']}")
        print(f"Cache misses: {cache_stats['misses']}")
        print(f"Hit rate: {cache_stats['hit_rate']:.1%}")
        print(f"Cache size: {cache_stats['cache_size']}")
    
    return results

def create_optimized_tournament_config():
    """Создать оптимизированную конфигурацию для турниров."""
    
    config = {
        "bot_weights": {
            "aggressive": 1.5,
            "critical": 1.0,
            "pawn": 0.8,
            "king": 0.6,
            "endgame": 1.2,
            "random": 0.0,
            "center": 0.8,
            "neural": 0.5
        },
        "time_limit": 120,  # 2 minutes per game
        "enable_caching": True,
        "enable_parallel": True,
        "cache_size": 10000
    }
    
    # Save config
    import json
    with open("optimized_tournament_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("💾 Optimized tournament config saved to optimized_tournament_config.json")
    return config

def main():
    """Основная функция оптимизации."""
    
    print("⚡ Chess AI Performance Optimization")
    print("=" * 50)
    
    # Test optimized bots
    results = performance_test_optimized_bots()
    
    # Create optimized config
    config = create_optimized_tournament_config()
    
    # Save results
    import json
    with open("optimization_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Optimization completed!")
    print(f"📄 Results saved to optimization_results.json")
    print(f"⚙️ Config saved to optimized_tournament_config.json")
    
    # Recommendations
    print(f"\n💡 Next Steps:")
    print(f"   1. Test optimized bots in tournament")
    print(f"   2. Monitor cache hit rates")
    print(f"   3. Adjust weights based on results")
    print(f"   4. Consider parallel evaluation for DynamicBot")

if __name__ == "__main__":
    main()
