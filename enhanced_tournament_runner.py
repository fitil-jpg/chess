#!/usr/bin/env python3
"""
Enhanced Tournament Runner with Optimizations and Progress Tracking
Покращений турнірний рушій з оптимізаціями та відстеженням прогресу
"""

import os
import sys
import time
import json
import logging
import itertools
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional, Any
import chess
import chess.engine

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tournament_optimization_progress import (
    TournamentOptimizer, OptimizationConfig, ProgressTracker,
    create_optimized_tournament_config
)
from chess_ai.bot_agent import get_agent_names, make_agent
from core.pst_trainer import update_from_board, update_from_history

# Setup logging
os.makedirs('tournament_logs', exist_ok=True)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedTournamentRunner:
    """Enhanced tournament runner with optimizations and progress tracking."""
    
    def __init__(self, config: Optional[OptimizationConfig] = None):
        self.config = config or create_optimized_tournament_config()
        self.optimizer = TournamentOptimizer(self.config)
        self.bot_names = self._get_optimized_bot_list()
        self.tournament_stats = {}
        self.tournament_patterns = []
        
        # Performance tracking
        self.total_time_savings = 0.0
        self.early_terminations = 0
        
        # Tournament settings
        self.games_per_match = int(os.environ.get('GAMES_PER_MATCH', '3'))
        self.time_per_game = int(os.environ.get('TIME_PER_GAME', '180'))
        
        # Create directories
        os.makedirs('tournament_logs', exist_ok=True)
        os.makedirs('tournament_patterns', exist_ok=True)
        os.makedirs('tournament_stats', exist_ok=True)
        
        logger.info(f"🏆 Enhanced Tournament Initialized")
        logger.info(f"🤖 Bots: {', '.join(self.bot_names)}")
        logger.info(f"⚡ Optimizations: Caching={self.config.enable_caching}, "
                   f"Parallel={self.config.enable_parallel_evaluation}")
    
    def _get_optimized_bot_list(self) -> List[str]:
        """Get optimized list of bots based on performance weights."""
        available_bots = get_agent_names()
        optimized_bots = self.optimizer.optimize_bot_selection(available_bots)
        
        logger.info(f"🎯 Selected {len(optimized_bots)} optimized bots from {len(available_bots)} available")
        return optimized_bots
    
    def run_tournament(self) -> Dict[str, Any]:
        """Run optimized tournament with progress tracking."""
        tournament_id = f"enhanced_tournament_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        tracker = ProgressTracker(tournament_id)
        
        tracker.add_checkpoint("Tournament started")
        
        # Generate matches
        matches = list(itertools.combinations(self.bot_names, 2))
        total_matches = len(matches)
        
        # Initialize tracking
        progress = self.optimizer.initialize_tournament(tournament_id, self.bot_names, matches)
        
        logger.info(f"📋 Total matches to play: {total_matches}")
        tracker.add_checkpoint(f"Generated {total_matches} matches")
        
        tournament_results = []
        
        for i, (bot1, bot2) in enumerate(matches, 1):
            # Update current match
            progress.current_match = (bot1, bot2)
            
            logger.info(f"⚔️  Match {i}/{total_matches}: {bot1} vs {bot2}")
            
            # Play optimized match
            match_result = self._play_optimized_match(bot1, bot2)
            tournament_results.append(match_result)
            
            # Update progress
            self.optimizer.update_match_progress(bot1, bot2, match_result)
            
            # Show intermediate standings
            if i % 5 == 0 or i == total_matches:
                self._show_current_standings(tournament_results)
                tracker.add_checkpoint(f"Completed {i}/{total_matches} matches")
            
            # Save intermediate results
            self._save_tournament_data(tournament_results, tournament_id)
            
            # Check optimization recommendations
            if i % 10 == 0:
                recommendations = self.optimizer.get_optimization_recommendations()
                if recommendations:
                    logger.info("💡 Optimization Recommendations:")
                    for rec in recommendations[:3]:  # Show top 3
                        logger.info(f"   {rec}")
        
        # Final calculations
        self._calculate_final_stats(tournament_results)
        tracker.add_checkpoint("Tournament completed")
        
        # Generate final report
        final_results = self._generate_final_report(tournament_results, tournament_id)
        
        # Save optimization report
        optimization_report = self.optimizer.save_optimization_report()
        
        logger.info(f"🏁 Tournament completed!")
        logger.info(f"📊 Progress report:\n{tracker.get_progress_report()}")
        logger.info(f"💾 Optimization report: {optimization_report}")
        
        return final_results
    
    def _play_optimized_match(self, bot1_name: str, bot2_name: str) -> Dict:
        """Play match with optimizations."""
        match_start_time = time.time()
        bot1_wins = 0
        bot2_wins = 0
        draws = 0
        games = []
        
        for game_num in range(1, self.games_per_match + 1):
            # Create bots
            bot1 = make_agent(bot1_name, chess.WHITE)
            bot2 = make_agent(bot2_name, chess.BLACK)
            
            # Play optimized game
            game_result = self._play_optimized_game(bot1, bot2, bot1_name, bot2_name, game_num)
            games.append(game_result)
            
            # Update score
            if game_result['result'] == '1-0':
                bot1_wins += 1
            elif game_result['result'] == '0-1':
                bot2_wins += 1
            else:
                draws += 1
            
            # Early termination if match is decided
            if bot1_wins > self.games_per_match // 2 or bot2_wins > self.games_per_match // 2:
                break
        
        # Determine winner
        if bot1_wins > bot2_wins:
            winner = bot1_name
        elif bot2_wins > bot1_wins:
            winner = bot2_name
        else:
            winner = "Draw"
        
        match_duration = time.time() - match_start_time
        
        match_result = {
            'bot1': bot1_name,
            'bot2': bot2_name,
            'bot1_wins': bot1_wins,
            'bot2_wins': bot2_wins,
            'draws': draws,
            'winner': winner,
            'games': games,
            'duration': match_duration,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"   Result: {bot1_wins}-{draws}-{bot2_wins} | Winner: {winner} | "
                   f"Time: {match_duration:.1f}s")
        
        return match_result
    
    def _play_optimized_game(self, bot1, bot2, bot1_name: str, bot2_name: str, game_num: int) -> Dict:
        """Play single game with optimizations."""
        board = chess.Board()
        moves = []
        fens = []
        start_time = time.time()
        
        # Track bot performance
        bot1_moves = 0
        bot2_moves = 0
        bot1_total_time = 0.0
        bot2_total_time = 0.0
        
        while not board.is_game_over() and (time.time() - start_time) < self.time_per_game:
            current_bot = bot1 if board.turn == chess.WHITE else bot2
            current_name = bot1_name if board.turn == chess.WHITE else bot2_name
            
            try:
                # Get board hash for caching
                board_hash = hashlib.sha256(board.fen().encode()).hexdigest()[:16]
                
                # Check cache first
                cached_result = self.optimizer.get_cached_evaluation(board_hash, current_name)
                if cached_result:
                    move = cached_result
                    logger.debug(f"🗄️ Cache hit for {current_name}")
                else:
                    # Get move with timing
                    move_start = time.time()
                    move_result = current_bot.choose_move(board)
                    move_time = time.time() - move_start
                    
                    # Cache the result
                    if move_result:
                        self.optimizer.cache_evaluation(board_hash, current_name, move_result)
                    
                    # Update timing
                    if current_name == bot1_name:
                        bot1_moves += 1
                        bot1_total_time += move_time
                    else:
                        bot2_moves += 1
                        bot2_total_time += move_time
                
                # Handle different return formats
                if move_result is None:
                    break
                elif isinstance(move_result, tuple):
                    move = move_result[0]
                    confidence = move_result[1] if len(move_result) > 1 else 0.5
                else:
                    move = move_result
                    confidence = 0.5
                
                # Early termination for high confidence moves
                if self.optimizer.should_terminate_early(board, confidence):
                    self.early_terminations += 1
                    logger.debug(f"⚡ Early termination for {current_name} (confidence: {confidence:.2f})")
                
                if move is None:
                    break
                
                # Validate move
                if move not in board.legal_moves:
                    logger.warning(f"Illegal move {move} for {current_name}")
                    # Track error
                    if self.optimizer.progress and current_name in self.optimizer.progress.bot_performance:
                        self.optimizer.progress.bot_performance[current_name]["errors"] += 1
                    break
                
                # Make move
                san_move = board.san(move)
                board.push(move)
                moves.append(san_move)
                fens.append(board.fen())
                
            except Exception as e:
                logger.error(f"Error in game {game_num}: {e}")
                # Track error
                if self.optimizer.progress and current_name in self.optimizer.progress.bot_performance:
                    self.optimizer.progress.bot_performance[current_name]["errors"] += 1
                break
        
        # Determine result
        if board.is_checkmate():
            result = "1-0" if board.turn == chess.BLACK else "0-1"
        elif board.is_stalemate() or board.is_insufficient_material() or board.is_seventyfive_moves():
            result = "1/2-1/2"
        else:
            result = "1/2-1/2"  # Time expired
        
        game_duration = time.time() - start_time
        
        # Update bot performance metrics
        if self.optimizer.progress:
            for bot_name, total_moves, total_time in [
                (bot1_name, bot1_moves, bot1_total_time),
                (bot2_name, bot2_moves, bot2_total_time)
            ]:
                if bot_name in self.optimizer.progress.bot_performance:
                    perf = self.optimizer.progress.bot_performance[bot_name]
                    perf["total_moves"] += total_moves
                    if total_moves > 0:
                        perf["avg_think_time"] = total_time / total_moves
        
        game_data = {
            'game_num': game_num,
            'white_bot': bot1_name,
            'black_bot': bot2_name,
            'result': result,
            'moves': moves,
            'fens': fens,
            'move_count': len(moves),
            'duration': game_duration,
            'timestamp': datetime.now().isoformat()
        }
        
        # Extract patterns if enough moves
        if len(moves) > 10:
            self._extract_patterns(board, moves, bot1_name, bot2_name, result)
        
        # Update PST tables for winner
        if result in ("1-0", "0-1"):
            winner = chess.WHITE if result == "1-0" else chess.BLACK
            update_from_board(board, winner)
            update_from_history(list(board.move_stack), winner, steps=[15, 21, 35])
        
        return game_data
    
    def _extract_patterns(self, board: chess.Board, moves: List[str], 
                          bot1_name: str, bot2_name: str, result: str):
        """Extract patterns from the game."""
        pattern_data = {
            'bot1': bot1_name,
            'bot2': bot2_name,
            'result': result,
            'moves': moves,
            'final_fen': board.fen(),
            'move_count': len(moves),
            'timestamp': datetime.now().isoformat()
        }
        self.tournament_patterns.append(pattern_data)
    
    def _show_current_standings(self, tournament_results: List[Dict]):
        """Display current tournament standings."""
        print("\n📊 Current Tournament Standings:")
        print("=" * 70)
        
        bot_stats = {}
        for bot_name in self.bot_names:
            bot_stats[bot_name] = {
                'wins': 0,
                'losses': 0,
                'draws': 0,
                'points': 0.0
            }
        
        for match in tournament_results:
            bot1 = match['bot1']
            bot2 = match['bot2']
            
            if match['winner'] == bot1:
                bot_stats[bot1]['wins'] += 1
                bot_stats[bot1]['points'] += 1.0
                bot_stats[bot2]['losses'] += 1
            elif match['winner'] == bot2:
                bot_stats[bot2]['wins'] += 1
                bot_stats[bot2]['points'] += 1.0
                bot_stats[bot1]['losses'] += 1
            else:
                bot_stats[bot1]['draws'] += 1
                bot_stats[bot2]['draws'] += 1
                bot_stats[bot1]['points'] += 0.5
                bot_stats[bot2]['points'] += 0.5
        
        # Sort by points
        sorted_bots = sorted(bot_stats.items(), key=lambda x: x[1]['points'], reverse=True)
        
        print(f"{'Rank':<6} {'Bot':<15} {'Points':<7} {'W-D-L':<9} {'Win %':<7}")
        print("-" * 70)
        
        for i, (bot_name, stats) in enumerate(sorted_bots, 1):
            total_games = stats['wins'] + stats['losses'] + stats['draws']
            win_pct = (stats['wins'] / total_games * 100) if total_games > 0 else 0
            print(f"{i:<6} {bot_name:<15} {stats['points']:<7.1f} "
                  f"{stats['wins']}-{stats['draws']}-{stats['losses']:<3} "
                  f"{win_pct:<7.1f}")
        
        print()
    
    def _calculate_final_stats(self, tournament_results: List[Dict]):
        """Calculate final tournament statistics."""
        bot_stats = {}
        
        for bot_name in self.bot_names:
            bot_stats[bot_name] = {
                'wins': 0,
                'losses': 0,
                'draws': 0,
                'matches_played': 0,
                'games_won': 0,
                'games_lost': 0,
                'games_drawn': 0
            }
        
        for match in tournament_results:
            bot1 = match['bot1']
            bot2 = match['bot2']
            
            # Update match stats
            bot_stats[bot1]['matches_played'] += 1
            bot_stats[bot2]['matches_played'] += 1
            
            if match['winner'] == bot1:
                bot_stats[bot1]['wins'] += 1
                bot_stats[bot2]['losses'] += 1
            elif match['winner'] == bot2:
                bot_stats[bot2]['wins'] += 1
                bot_stats[bot1]['losses'] += 1
            else:
                bot_stats[bot1]['draws'] += 1
                bot_stats[bot2]['draws'] += 1
            
            # Update game stats
            bot_stats[bot1]['games_won'] += match['bot1_wins']
            bot_stats[bot1]['games_lost'] += match['bot2_wins']
            bot_stats[bot1]['games_drawn'] += match['draws']
            
            bot_stats[bot2]['games_won'] += match['bot2_wins']
            bot_stats[bot2]['games_lost'] += match['bot1_wins']
            bot_stats[bot2]['games_drawn'] += match['draws']
        
        # Sort by wins
        sorted_bots = sorted(bot_stats.items(), key=lambda x: (x[1]['wins'], x[1]['games_won']), reverse=True)
        
        self.tournament_stats = {
            'bot_rankings': sorted_bots,
            'total_matches': len(tournament_results),
            'total_games': sum(match['bot1_wins'] + match['bot2_wins'] + match['draws'] for match in tournament_results),
            'timestamp': datetime.now().isoformat(),
            'optimization_stats': {
                'early_terminations': self.early_terminations,
                'time_savings': self.total_time_savings,
                'cache_hits': self.optimizer.optimization_stats['cache_hits'],
                'cache_misses': self.optimizer.optimization_stats['cache_misses']
            }
        }
    
    def _save_tournament_data(self, tournament_results: List[Dict], tournament_id: str):
        """Save tournament data to files."""
        # Save results
        with open(f'tournament_stats/{tournament_id}_matches.json', 'w', encoding='utf-8') as f:
            json.dump(tournament_results, f, ensure_ascii=False, indent=2)
        
        # Save patterns
        with open(f'tournament_patterns/{tournament_id}_patterns.json', 'w', encoding='utf-8') as f:
            json.dump(self.tournament_patterns, f, ensure_ascii=False, indent=2)
        
        # Save bot metrics
        if self.optimizer.progress:
            with open(f'tournament_stats/{tournament_id}_bot_metrics.json', 'w', encoding='utf-8') as f:
                json.dump(self.optimizer.progress.bot_performance, f, ensure_ascii=False, indent=2)
    
    def _generate_final_report(self, tournament_results: List[Dict], tournament_id: str) -> Dict[str, Any]:
        """Generate comprehensive final report."""
        final_results = {
            'tournament_id': tournament_id,
            'tournament_stats': self.tournament_stats,
            'matches': tournament_results,
            'patterns': self.tournament_patterns,
            'bot_performance': self.optimizer.progress.bot_performance if self.optimizer.progress else {},
            'optimization_config': {
                'caching_enabled': self.config.enable_caching,
                'parallel_evaluation': self.config.enable_parallel_evaluation,
                'cache_size': self.config.cache_size,
                'early_termination_threshold': self.config.early_termination_threshold
            }
        }
        
        # Save full results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'tournament_stats/final_results_{timestamp}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, ensure_ascii=False, indent=2)
        
        # Create readable report
        self._create_readable_report(tournament_id, timestamp)
        
        logger.info(f"📄 Final report saved: {filename}")
        return final_results
    
    def _create_readable_report(self, tournament_id: str, timestamp: str):
        """Create readable text report."""
        report_path = f'tournament_stats/{tournament_id}_report_{timestamp}.txt'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=== ENHANCED TOURNAMENT REPORT ===\n\n")
            f.write(f"Tournament ID: {tournament_id}\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Bots: {len(self.bot_names)}\n")
            f.write(f"Matches: {self.tournament_stats['total_matches']}\n")
            f.write(f"Games: {self.tournament_stats['total_games']}\n")
            f.write(f"Games per match: {self.games_per_match}\n")
            f.write(f"Time per game: {self.time_per_game}s\n\n")
            
            f.write("=== OPTIMIZATION STATS ===\n")
            opt_stats = self.tournament_stats['optimization_stats']
            f.write(f"Early terminations: {opt_stats['early_terminations']}\n")
            f.write(f"Time savings: {opt_stats['time_savings']:.1f}s\n")
            f.write(f"Cache hits: {opt_stats['cache_hits']}\n")
            f.write(f"Cache misses: {opt_stats['cache_misses']}\n")
            
            total_requests = opt_stats['cache_hits'] + opt_stats['cache_misses']
            if total_requests > 0:
                hit_rate = opt_stats['cache_hits'] / total_requests * 100
                f.write(f"Cache hit rate: {hit_rate:.1f}%\n")
            
            f.write("\n=== FINAL RANKINGS ===\n")
            for i, (bot_name, stats) in enumerate(self.tournament_stats['bot_rankings'], 1):
                f.write(f"{i}. {bot_name}:\n")
                f.write(f"   Matches: {stats['wins']}W-{stats['losses']}L-{stats['draws']}D\n")
                f.write(f"   Games: {stats['games_won']}W-{stats['games_lost']}L-{stats['games_drawn']}D\n\n")
        
        logger.info(f"📄 Readable report saved: {report_path}")

def main():
    """Main function to run enhanced tournament."""
    try:
        print("🚀 Starting Enhanced Chess AI Tournament")
        print("=" * 50)
        
        # Create optimized configuration
        config = create_optimized_tournament_config()
        
        # Create and run tournament
        runner = EnhancedTournamentRunner(config)
        results = runner.run_tournament()
        
        print("✅ Enhanced tournament completed successfully!")
        print(f"📊 Total matches: {results['tournament_stats']['total_matches']}")
        print(f"🎮 Total games: {results['tournament_stats']['total_games']}")
        
        # Show optimization benefits
        opt_stats = results['tournament_stats']['optimization_stats']
        print(f"⚡ Early terminations: {opt_stats['early_terminations']}")
        print(f"🗄️ Cache efficiency: {opt_stats['cache_hits']}/{opt_stats['cache_hits'] + opt_stats['cache_misses']}")
        
    except KeyboardInterrupt:
        print("\n⏹️  Tournament interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Tournament error: {e}")
        logger.error(f"Tournament failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
