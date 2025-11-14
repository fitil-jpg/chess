#!/usr/bin/env python3
"""
Automated Tournament Testing System
Автоматичне тестування на турнірах зі збором метрик
"""

import os
import sys
import time
import json
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AutomatedTournamentTester:
    """Автоматизована система тестування турнірів."""
    
    def __init__(self, tournament_script: str = "run_clean_tournament.py"):
        self.tournament_script = tournament_script
        self.results_dir = Path("tournament_stats")
        self.test_results = []
        
    def run_tournament_test(self, config: Dict) -> Dict:
        """Запустити турнір з заданою конфігурацією."""
        
        test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"🚀 Starting tournament test: {test_id}")
        
        # Prepare environment
        env = os.environ.copy()
        
        # Set configuration via environment variables
        if 'bot_weights' in config:
            env['CHESS_BOT_WEIGHTS'] = json.dumps(config['bot_weights'])
        
        if 'time_limit' in config:
            env['CHESS_TIME_LIMIT'] = str(config['time_limit'])
        
        # Run tournament
        start_time = time.time()
        
        try:
            result = subprocess.run(
                [sys.executable, self.tournament_script],
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour timeout
                env=env
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse results
            if result.returncode == 0:
                results = self._parse_tournament_output(result.stdout)
                results.update({
                    'test_id': test_id,
                    'config': config,
                    'duration': duration,
                    'timestamp': datetime.now().isoformat(),
                    'success': True
                })
                
                logger.info(f"✅ Tournament {test_id} completed in {duration:.1f}s")
                return results
            else:
                logger.error(f"❌ Tournament {test_id} failed: {result.stderr}")
                return {
                    'test_id': test_id,
                    'config': config,
                    'duration': duration,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': result.stderr
                }
                
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ Tournament {test_id} timed out")
            return {
                'test_id': test_id,
                'config': config,
                'duration': 3600,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': 'Timeout'
            }
        except Exception as e:
            logger.error(f"💥 Tournament {test_id} crashed: {e}")
            return {
                'test_id': test_id,
                'config': config,
                'duration': time.time() - start_time,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            }
    
    def _parse_tournament_output(self, output: str) -> Dict:
        """Парсити вивід турніру для отримання результатів."""
        
        results = {
            'standings': [],
            'metrics': {}
        }
        
        lines = output.split('\n')
        current_standings = []
        
        for line in lines:
            line = line.strip()
            
            # Parse final standings
            if '🏆 Фінальна таблиця турніру:' in line or '🏆 Final tournament standings:' in line:
                # Next lines contain standings
                continue
            
            # Parse standing lines
            if line and line[0].isdigit() and '.' in line:
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        position = int(parts[0].rstrip('.'))
                        name = parts[1]
                        points = float(parts[2])
                        games = int(parts[3])
                        
                        # Extract additional metrics if available
                        wins = losses = draws = 0
                        avg_time = 0.0
                        
                        for i, part in enumerate(parts):
                            if 'wins' in part.lower() and i > 0:
                                wins = int(parts[i-1])
                            elif 'losses' in part.lower() and i > 0:
                                losses = int(parts[i-1])
                            elif 'draws' in part.lower() and i > 0:
                                draws = int(parts[i-1])
                        
                        current_standings.append({
                            'position': position,
                            'name': name,
                            'points': points,
                            'games_played': games,
                            'wins': wins,
                            'losses': losses,
                            'draws': draws
                        })
                    except (ValueError, IndexError):
                        continue
        
        results['standings'] = current_standings
        
        # Calculate tournament metrics
        if current_standings:
            total_points = sum(s['points'] for s in current_standings)
            total_games = sum(s['games_played'] for s in current_standings)
            
            results['metrics'] = {
                'total_points': total_points,
                'total_games': total_games,
                'avg_points_per_game': total_points / max(1, total_games),
                'participants': len(current_standings)
            }
        
        return results
    
    def run_test_suite(self, test_configs: List[Dict]) -> List[Dict]:
        """Запустити набір тестів з різними конфігураціями."""
        
        logger.info(f"🎯 Running test suite with {len(test_configs)} configurations")
        
        results = []
        
        for i, config in enumerate(test_configs, 1):
            logger.info(f"📍 Test {i}/{len(test_configs)}: {config.get('name', 'Unnamed')}")
            
            result = self.run_tournament_test(config)
            results.append(result)
            
            # Small delay between tests
            time.sleep(2)
        
        self.test_results = results
        return results
    
    def analyze_test_results(self, results: List[Dict]) -> Dict:
        """Проаналізувати результати тестів."""
        
        analysis = {
            'summary': {},
            'best_configurations': {},
            'performance_comparison': {},
            'recommendations': []
        }
        
        # Filter successful tests
        successful_tests = [r for r in results if r.get('success', False)]
        
        if not successful_tests:
            analysis['summary'] = {
                'total_tests': len(results),
                'successful_tests': 0,
                'success_rate': 0.0
            }
            return analysis
        
        # Overall summary
        analysis['summary'] = {
            'total_tests': len(results),
            'successful_tests': len(successful_tests),
            'success_rate': len(successful_tests) / len(results),
            'avg_duration': sum(r['duration'] for r in successful_tests) / len(successful_tests)
        }
        
        # Find best configurations
        best_overall = max(successful_tests, key=lambda x: x['metrics'].get('avg_points_per_game', 0))
        analysis['best_configurations']['overall_performance'] = best_overall
        
        # Performance comparison by configuration type
        config_performance = {}
        
        for result in successful_tests:
            config_name = result['config'].get('name', 'default')
            
            if config_name not in config_performance:
                config_performance[config_name] = []
            
            config_performance[config_name].append(result['metrics'].get('avg_points_per_game', 0))
        
        # Calculate averages for each configuration
        for config_name, scores in config_performance.items():
            analysis['performance_comparison'][config_name] = {
                'avg_score': sum(scores) / len(scores),
                'max_score': max(scores),
                'min_score': min(scores),
                'test_count': len(scores)
            }
        
        # Generate recommendations
        analysis['recommendations'] = self._generate_recommendations(analysis)
        
        return analysis
    
    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Згенерувати рекомендації на основі аналізу."""
        
        recommendations = []
        
        # Success rate recommendations
        success_rate = analysis['summary']['success_rate']
        if success_rate < 0.8:
            recommendations.append(
                f"⚠️ Low success rate ({success_rate:.1%}) - check tournament stability and error handling"
            )
        
        # Performance recommendations
        if 'performance_comparison' in analysis:
            best_config = max(analysis['performance_comparison'].items(), 
                            key=lambda x: x[1]['avg_score'])
            
            recommendations.append(
                f"🏆 Best performing configuration: {best_config[0]} "
                f"(avg score: {best_config[1]['avg_score']:.2f})"
            )
            
            # Suggest improvements for lower-performing configs
            for config_name, perf in analysis['performance_comparison'].items():
                if perf['avg_score'] < best_config[1]['avg_score'] * 0.9:
                    recommendations.append(
                        f"📈 Consider optimizing {config_name} - "
                        f"performance {perf['avg_score']:.2f} vs best {best_config[1]['avg_score']:.2f}"
                    )
        
        return recommendations
    
    def create_test_report(self, results: List[Dict], analysis: Dict) -> str:
        """Створити звіт про тестування."""
        
        report = []
        report.append("# 🤖 Automated Tournament Testing Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary
        summary = analysis['summary']
        report.append("## 📊 Summary")
        report.append(f"- Total tests: {summary['total_tests']}")
        report.append(f"- Successful: {summary['successful_tests']}")
        report.append(f"- Success rate: {summary['success_rate']:.1%}")
        report.append(f"- Average duration: {summary['avg_duration']:.1f}s")
        report.append("")
        
        # Best configurations
        if 'best_configurations' in analysis:
            best = analysis['best_configurations'].get('overall_performance')
            if best:
                report.append("## 🏆 Best Configuration")
                report.append(f"Name: {best['config'].get('name', 'default')}")
                report.append(f"Score: {best['metrics'].get('avg_points_per_game', 0):.2f}")
                report.append(f"Duration: {best['duration']:.1f}s")
                report.append("")
        
        # Performance comparison
        if 'performance_comparison' in analysis:
            report.append("## 📈 Performance Comparison")
            for config_name, perf in analysis['performance_comparison'].items():
                report.append(f"**{config_name}**:")
                report.append(f"- Average score: {perf['avg_score']:.2f}")
                report.append(f"- Range: {perf['min_score']:.2f} - {perf['max_score']:.2f}")
                report.append(f"- Tests: {perf['test_count']}")
                report.append("")
        
        # Recommendations
        if analysis['recommendations']:
            report.append("## 💡 Recommendations")
            for rec in analysis['recommendations']:
                report.append(f"- {rec}")
            report.append("")
        
        # Detailed results
        report.append("## 📋 Detailed Results")
        for result in results:
            status = "✅" if result.get('success', False) else "❌"
            report.append(f"{status} **{result['config'].get('name', 'test')}** "
                         f"({result['duration']:.1f}s)")
            
            if result.get('success', False):
                metrics = result.get('metrics', {})
                report.append(f"   Score: {metrics.get('avg_points_per_game', 0):.2f}, "
                             f"Games: {metrics.get('total_games', 0)}")
            else:
                report.append(f"   Error: {result.get('error', 'Unknown')}")
            report.append("")
        
        return "\n".join(report)

def create_test_configurations() -> List[Dict]:
    """Створити конфігурації для тестування."""
    
    configs = [
        {
            'name': 'default',
            'description': 'Default configuration'
        },
        {
            'name': 'aggressive_focused',
            'bot_weights': {
                'aggressive': 2.0,
                'critical': 1.0,
                'pawn': 0.5,
                'king': 0.8
            },
            'description': 'Emphasis on aggressive play'
        },
        {
            'name': 'pawn_focused',
            'bot_weights': {
                'aggressive': 0.8,
                'critical': 1.0,
                'pawn': 2.0,
                'king': 1.2
            },
            'description': 'Emphasis on pawn structure'
        },
        {
            'name': 'balanced',
            'bot_weights': {
                'aggressive': 1.2,
                'critical': 1.2,
                'pawn': 1.2,
                'king': 1.2
            },
            'description': 'Balanced all-around approach'
        },
        {
            'name': 'fast_games',
            'time_limit': 60,
            'description': 'Shorter time limit for faster games'
        }
    ]
    
    return configs

def main():
    """Основна функція автоматизованого тестування."""
    
    print("🤖 Automated Tournament Testing System")
    print("=" * 50)
    
    # Check if tournament script exists
    if not os.path.exists("run_clean_tournament.py"):
        print("❌ Tournament script 'run_clean_tournament.py' not found!")
        return
    
    tester = AutomatedTournamentTester()
    
    # Create test configurations
    configs = create_test_configurations()
    
    print(f"🎯 Running {len(configs)} test configurations...")
    
    # Run test suite
    results = tester.run_test_suite(configs)
    
    # Analyze results
    print("📊 Analyzing results...")
    analysis = tester.analyze_test_results(results)
    
    # Create report
    print("📝 Generating report...")
    report = tester.create_test_report(results, analysis)
    
    # Save report
    report_file = f"tournament_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    # Save raw results
    results_file = f"tournament_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'analysis': analysis
        }, f, indent=2, default=str)
    
    print(f"\n✅ Testing completed!")
    print(f"📄 Report saved to: {report_file}")
    print(f"💾 Raw data saved to: {results_file}")
    
    # Print summary
    summary = analysis['summary']
    print(f"\n📊 Summary:")
    print(f"   Success rate: {summary['success_rate']:.1%}")
    print(f"   Average duration: {summary['avg_duration']:.1f}s")
    
    if analysis['recommendations']:
        print(f"\n💡 Top recommendations:")
        for rec in analysis['recommendations'][:3]:
            print(f"   {rec}")

if __name__ == "__main__":
    main()
