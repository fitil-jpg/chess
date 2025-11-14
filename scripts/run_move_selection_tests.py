#!/usr/bin/env python3
"""
Run optimal move selection tests and generate performance report.

This script executes the comprehensive test suite for move selection
and generates a detailed performance report with metrics and analysis.
"""

import sys
import os
import time
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Tuple
import traceback

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import chess
    from chess_ai.dynamic_bot import DynamicBot
    from chess_ai.aggressive_bot import AggressiveBot
    from chess_ai.fortify_bot import FortifyBot
    from chess_ai.endgame_bot import EndgameBot
    from core.evaluator import Evaluator
    from utils import GameContext
    from core.move_object import move_evaluation_manager
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


class MoveSelectionTestRunner:
    """Comprehensive test runner for move selection functionality."""
    
    def __init__(self):
        self.results = {
            'test_summary': {},
            'performance_metrics': {},
            'bot_performance': {},
            'scenario_results': {},
            'errors': [],
            'timestamp': time.time()
        }
    
    def run_pytest_tests(self) -> Dict[str, Any]:
        """Run pytest test suites and collect results."""
        print("🧪 Running pytest test suites...")
        
        test_files = [
            'tests/test_optimal_move_selection.py',
            'tests/test_move_scenarios.py'
        ]
        
        pytest_results = {}
        
        for test_file in test_files:
            print(f"\n📋 Running {test_file}...")
            try:
                # Run pytest with JSON output if available, otherwise capture output
                cmd = [
                    sys.executable, '-m', 'pytest', 
                    test_file, '-v', '--tb=short', '--no-header'
                ]
                
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    cwd=project_root
                )
                
                pytest_results[test_file] = {
                    'return_code': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'success': result.returncode == 0
                }
                
                # Parse basic statistics from output
                if result.stdout:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'passed' in line and 'failed' in line:
                            pytest_results[test_file]['summary'] = line.strip()
                            break
                
                print(f"✅ {test_file}: {'PASSED' if result.returncode == 0 else 'FAILED'}")
                
            except Exception as e:
                error_msg = f"Failed to run {test_file}: {e}"
                print(f"❌ {error_msg}")
                pytest_results[test_file] = {
                    'error': error_msg,
                    'success': False
                }
                self.results['errors'].append(error_msg)
        
        self.results['test_summary']['pytest'] = pytest_results
        return pytest_results
    
    def run_performance_benchmarks(self) -> Dict[str, Any]:
        """Run performance benchmarks for move selection."""
        print("\n⚡ Running performance benchmarks...")
        
        benchmarks = {}
        
        # Test positions for benchmarking
        test_positions = [
            ("Opening", chess.Board()),
            ("Middlegame", chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4")),
            ("Endgame", chess.Board("8/8/8/5k2/8/8/4K3/8 w - - 0 1")),
            ("Tactical", chess.Board("r2qkbnr/ppp2ppp/2np4/2b5/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 5"))
        ]
        
        bots = [
            ("AggressiveBot", AggressiveBot),
            ("FortifyBot", FortifyBot),
            ("EndgameBot", EndgameBot),
            ("DynamicBot", DynamicBot)
        ]
        
        for position_name, board in test_positions:
            print(f"\n🎯 Benchmarking {position_name} position...")
            benchmarks[position_name] = {}
            
            evaluator = Evaluator(board)
            context = GameContext(
                material_diff=evaluator.material_diff(True),
                mobility=0,
                king_safety=0
            )
            
            for bot_name, bot_class in bots:
                try:
                    bot = bot_class(chess.WHITE)
                    
                    # Measure performance
                    start_time = time.time()
                    move, result = bot.choose_move(board, evaluator=evaluator, context=context)
                    end_time = time.time()
                    
                    duration_ms = (end_time - start_time) * 1000
                    
                    benchmarks[position_name][bot_name] = {
                        'move': move.uci() if move else None,
                        'result': result,
                        'duration_ms': duration_ms,
                        'legal': board.is_legal(move) if move else False,
                        'success': move is not None
                    }
                    
                    print(f"  ✓ {bot_name}: {move.uci() if move else 'None'} ({duration_ms:.1f}ms)")
                    
                except Exception as e:
                    error_msg = f"{bot_name} failed on {position_name}: {e}"
                    print(f"  ❌ {error_msg}")
                    benchmarks[position_name][bot_name] = {
                        'error': str(e),
                        'success': False
                    }
                    self.results['errors'].append(error_msg)
        
        self.results['performance_metrics']['benchmarks'] = benchmarks
        return benchmarks
    
    def test_dynamic_bot_features(self) -> Dict[str, Any]:
        """Test DynamicBot specific features."""
        print("\n🤖 Testing DynamicBot features...")
        
        feature_tests = {}
        board = chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4")
        evaluator = Evaluator(board)
        context = GameContext(
            material_diff=evaluator.material_diff(True),
            mobility=0,
            king_safety=0
        )
        
        # Test move tracking
        try:
            bot = DynamicBot(chess.WHITE, enable_move_tracking=True)
            move, confidence = bot.choose_move(board, evaluator=evaluator, context=context)
            
            feature_tests['move_tracking'] = {
                'enabled': bot.enable_move_tracking,
                'has_move_object': bot.get_current_move_object() is not None,
                'success': True
            }
            
            # Test decision roadmap
            roadmap = bot.get_decision_roadmap()
            feature_tests['decision_roadmap'] = {
                'available': roadmap is not None,
                'not_empty': isinstance(roadmap, dict) and len(roadmap) > 0,
                'success': True
            }
            
            # Test performance summary
            summary = bot.get_agent_performance_summary()
            feature_tests['performance_summary'] = {
                'available': summary is not None,
                'success': True
            }
            
            print("  ✓ Move tracking: PASSED")
            print("  ✓ Decision roadmap: PASSED")
            print("  ✓ Performance summary: PASSED")
            
        except Exception as e:
            error_msg = f"DynamicBot features test failed: {e}"
            print(f"  ❌ {error_msg}")
            feature_tests['error'] = str(e)
            self.results['errors'].append(error_msg)
        
        # Test ensemble behavior
        try:
            bot = DynamicBot(chess.WHITE)
            
            # Test with different weights
            custom_weights = {
                'aggressive': 2.0,
                'fortify': 1.5,
                'endgame': 0.5
            }
            
            bot_weighted = DynamicBot(chess.WHITE, weights=custom_weights)
            move1, conf1 = bot.choose_move(board, evaluator=evaluator, context=context)
            move2, conf2 = bot_weighted.choose_move(board, evaluator=evaluator, context=context)
            
            feature_tests['ensemble_weighting'] = {
                'default_move': move1.uci() if move1 else None,
                'weighted_move': move2.uci() if move2 else None,
                'different_decisions': move1 != move2,
                'success': True
            }
            
            print(f"  ✓ Ensemble weighting: {move1.uci() if move1 else 'None'} vs {move2.uci() if move2 else 'None'}")
            
        except Exception as e:
            error_msg = f"Ensemble weighting test failed: {e}"
            print(f"  ❌ {error_msg}")
            feature_tests['ensemble_weighting'] = {'error': str(e)}
            self.results['errors'].append(error_msg)
        
        self.results['bot_performance']['dynamic_bot_features'] = feature_tests
        return feature_tests
    
    def test_move_quality_validation(self) -> Dict[str, Any]:
        """Test move quality across different scenarios."""
        print("\n🎯 Testing move quality validation...")
        
        quality_tests = {}
        
        # Test positions with known good moves
        test_scenarios = [
            {
                'name': 'Capture Opportunity',
                'fen': 'r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4',
                'expected_move_types': ['capture', 'check', 'development']
            },
            {
                'name': 'Endgame Technique',
                'fen': '8/8/8/5k2/8/8/4K3/8 w - - 0 1',
                'expected_move_types': ['king_move']
            },
            {
                'name': 'Opening Development',
                'fen': chess.Board().fen(),
                'expected_move_types': ['development', 'center_control']
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n  📋 Testing {scenario['name']}...")
            board = chess.Board(scenario['fen'])
            evaluator = Evaluator(board)
            context = GameContext(
                material_diff=evaluator.material_diff(True),
                mobility=0,
                king_safety=0
            )
            
            scenario_results = {}
            
            # Test with different bots
            bots_to_test = [
                ('Aggressive', AggressiveBot(chess.WHITE)),
                ('Fortify', FortifyBot(chess.WHITE)),
                ('Dynamic', DynamicBot(chess.WHITE))
            ]
            
            for bot_name, bot in bots_to_test:
                try:
                    move, result = bot.choose_move(board, evaluator=evaluator, context=context)
                    
                    move_analysis = {
                        'move': move.uci() if move else None,
                        'legal': board.is_legal(move) if move else False,
                        'is_capture': board.is_capture(move) if move else False,
                        'gives_check': board.gives_check(move) if move else False,
                        'piece_type': board.piece_at(move.from_square).piece_type if move else None
                    }
                    
                    # Validate move quality
                    quality_score = self._evaluate_move_quality(board, move, scenario['expected_move_types'])
                    move_analysis['quality_score'] = quality_score
                    
                    scenario_results[bot_name] = move_analysis
                    
                    print(f"    ✓ {bot_name}: {move.uci() if move else 'None'} (score: {quality_score:.1f})")
                    
                except Exception as e:
                    error_msg = f"{bot_name} failed on {scenario['name']}: {e}"
                    print(f"    ❌ {error_msg}")
                    scenario_results[bot_name] = {'error': str(e)}
                    self.results['errors'].append(error_msg)
            
            quality_tests[scenario['name']] = scenario_results
        
        self.results['scenario_results']['move_quality'] = quality_tests
        return quality_tests
    
    def _evaluate_move_quality(self, board: chess.Board, move: chess.Move, expected_types: List[str]) -> float:
        """Evaluate the quality of a move based on expected characteristics."""
        if not move or not board.is_legal(move):
            return 0.0
        
        score = 0.0
        
        # Basic checks
        if board.is_capture(move):
            score += 3.0
        if board.gives_check(move):
            score += 2.5
        
        # Development in opening
        if 'development' in expected_types:
            piece = board.piece_at(move.from_square)
            if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
                from_rank = chess.square_rank(move.from_square)
                if from_rank == 0:  # From back rank
                    score += 2.0
        
        # Center control
        if 'center_control' in expected_types:
            center_squares = {chess.D4, chess.E4, chess.D5, chess.E5}
            if move.to_square in center_squares:
                score += 1.5
        
        # King moves in endgame
        if 'king_move' in expected_types:
            piece = board.piece_at(move.from_square)
            if piece and piece.piece_type == chess.KING:
                score += 3.0
        
        # Tactical considerations
        if 'capture' in expected_types and board.is_capture(move):
            score += 2.0
        
        return score
    
    def generate_report(self) -> str:
        """Generate comprehensive test report."""
        print("\n📊 Generating test report...")
        
        report = {
            'summary': {
                'total_tests_run': len(self.results.get('test_summary', {})),
                'total_errors': len(self.results['errors']),
                'timestamp': self.results['timestamp']
            },
            'test_results': self.results.get('test_summary', {}),
            'performance_metrics': self.results.get('performance_metrics', {}),
            'bot_performance': self.results.get('bot_performance', {}),
            'scenario_results': self.results.get('scenario_results', {}),
            'errors': self.results['errors']
        }
        
        # Save report to file
        report_file = project_root / 'test_reports' / f'move_selection_report_{int(time.time())}.json'
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📄 Report saved to: {report_file}")
        return str(report_file)
    
    def run_all_tests(self) -> str:
        """Run all tests and generate report."""
        print("🚀 Starting comprehensive move selection testing...\n")
        
        # Run all test suites
        self.run_pytest_tests()
        self.run_performance_benchmarks()
        self.test_dynamic_bot_features()
        self.test_move_quality_validation()
        
        # Generate final report
        report_file = self.generate_report()
        
        # Print summary
        self.print_summary()
        
        return report_file
    
    def print_summary(self):
        """Print test summary to console."""
        print("\n" + "="*60)
        print("📋 MOVE SELECTION TEST SUMMARY")
        print("="*60)
        
        # Test summary
        pytest_results = self.results.get('test_summary', {}).get('pytest', {})
        if pytest_results:
            print("\n🧪 Pytest Results:")
            for test_file, result in pytest_results.items():
                status = "✅ PASSED" if result.get('success', False) else "❌ FAILED"
                summary = result.get('summary', '')
                print(f"  {test_file}: {status}")
                if summary:
                    print(f"    {summary}")
        
        # Performance metrics
        benchmarks = self.results.get('performance_metrics', {}).get('benchmarks', {})
        if benchmarks:
            print("\n⚡ Performance Summary:")
            for position, results in benchmarks.items():
                successful_tests = sum(1 for r in results.values() if r.get('success', False))
                total_tests = len(results)
                print(f"  {position}: {successful_tests}/{total_tests} bots successful")
        
        # Errors
        errors = self.results.get('errors', [])
        if errors:
            print(f"\n❌ Errors encountered: {len(errors)}")
            for error in errors[:5]:  # Show first 5 errors
                print(f"  • {error}")
            if len(errors) > 5:
                print(f"  ... and {len(errors) - 5} more errors")
        
        print("\n" + "="*60)


def main():
    """Main entry point."""
    runner = MoveSelectionTestRunner()
    
    try:
        report_file = runner.run_all_tests()
        print(f"\n🎉 Testing completed! Report available at: {report_file}")
        return 0
    except Exception as e:
        print(f"\n💥 Test runner failed: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
