#!/usr/bin/env python3
"""
Metrics-Driven Bot Improvement System
Анализ турнірних метрик для вдосконалення ботів
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Tuple, Any
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricsAnalyzer:
    """Анализатор метрик для улучшения ботів."""
    
    def __init__(self, results_dir: str = "tournament_stats"):
        self.results_dir = Path(results_dir)
        self.metrics = {}
        
    def load_tournament_results(self) -> Dict:
        """Загрузить результаты турниров."""
        
        results = {}
        
        # Ищем JSON файлы с результатами
        json_files = list(self.results_dir.glob("final_results_*.json"))
        
        for file_path in json_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    timestamp = file_path.stem.split('_')[-1]
                    results[timestamp] = data
                    logger.info(f"Loaded tournament from {timestamp}")
            except Exception as e:
                logger.warning(f"Failed to load {file_path}: {e}")
        
        return results
    
    def analyze_bot_performance(self, results: Dict) -> Dict:
        """Проанализировать производительность ботов."""
        
        bot_stats = {}
        
        for timestamp, tournament_data in results.items():
            if 'standings' not in tournament_data:
                continue
                
            for bot_result in tournament_data['standings']:
                bot_name = bot_result['name']
                
                if bot_name not in bot_stats:
                    bot_stats[bot_name] = {
                        'tournaments': 0,
                        'total_points': 0,
                        'total_games': 0,
                        'wins': 0,
                        'losses': 0,
                        'draws': 0,
                        'avg_think_time': [],
                        'performance_history': []
                    }
                
                stats = bot_stats[bot_name]
                stats['tournaments'] += 1
                stats['total_points'] += bot_result['points']
                stats['total_games'] += bot_result['games_played']
                stats['wins'] += bot_result.get('wins', 0)
                stats['losses'] += bot_result.get('losses', 0)
                stats['draws'] += bot_result.get('draws', 0)
                
                if 'avg_think_time' in bot_result:
                    stats['avg_think_time'].append(bot_result['avg_think_time'])
                
                # Performance metrics
                win_rate = bot_result.get('wins', 0) / max(1, bot_result.get('games_played', 1))
                points_per_game = bot_result['points'] / max(1, bot_result['games_played'])
                
                stats['performance_history'].append({
                    'timestamp': timestamp,
                    'win_rate': win_rate,
                    'points_per_game': points_per_game,
                    'standing': bot_result.get('position', 0)
                })
        
        # Calculate aggregates
        for bot_name, stats in bot_stats.items():
            stats['overall_win_rate'] = stats['wins'] / max(1, stats['total_games'])
            stats['points_per_game'] = stats['total_points'] / max(1, stats['total_games'])
            stats['avg_think_time'] = np.mean(stats['avg_think_time']) if stats['avg_think_time'] else 0
            
            # Performance trend (last 3 tournaments vs all previous)
            if len(stats['performance_history']) >= 4:
                recent = stats['performance_history'][-3:]
                previous = stats['performance_history'][:-3]
                
                recent_wr = np.mean([h['win_rate'] for h in recent])
                previous_wr = np.mean([h['win_rate'] for h in previous])
                
                stats['trend'] = recent_wr - previous_wr
            else:
                stats['trend'] = 0.0
        
        return bot_stats
    
    def generate_improvement_recommendations(self, bot_stats: Dict) -> Dict:
        """Сгенерировать рекомендации по улучшению."""
        
        recommendations = {}
        
        for bot_name, stats in bot_stats.items():
            bot_recs = []
            
            # Performance based recommendations
            if stats['overall_win_rate'] < 0.3:
                bot_recs.append({
                    'priority': 'HIGH',
                    'category': 'PERFORMANCE',
                    'issue': f'Low win rate ({stats["overall_win_rate"]:.1%})',
                    'suggestion': 'Consider increasing search depth or improving evaluation function'
                })
            elif stats['overall_win_rate'] > 0.7:
                bot_recs.append({
                    'priority': 'MEDIUM',
                    'category': 'BALANCE',
                    'issue': f'Very high win rate ({stats["overall_win_rate"]:.1%})',
                    'suggestion': 'Bot may be too strong - consider adding variety or testing against stronger opponents'
                })
            
            # Speed based recommendations
            if stats['avg_think_time'] > 1.0:
                bot_recs.append({
                    'priority': 'HIGH',
                    'category': 'PERFORMANCE',
                    'issue': f'Slow decision making ({stats["avg_think_time"]:.2f}s avg)',
                    'suggestion': 'Implement caching, reduce search depth, or optimize evaluation'
                })
            
            # Trend based recommendations
            if stats['trend'] < -0.1:
                bot_recs.append({
                    'priority': 'HIGH',
                    'category': 'REGRESSION',
                    'issue': f'Declining performance trend ({stats["trend"]:.1%})',
                    'suggestion': 'Recent changes may have degraded performance - review recent modifications'
                })
            elif stats['trend'] > 0.1:
                bot_recs.append({
                    'priority': 'LOW',
                    'category': 'IMPROVEMENT',
                    'issue': f'Improving performance trend ({stats["trend"]:.1%})',
                    'suggestion': 'Recent changes are working well - consider applying similar improvements to other bots'
                })
            
            # Bot-specific recommendations
            bot_recs.extend(self._get_bot_specific_recommendations(bot_name, stats))
            
            recommendations[bot_name] = bot_recs
        
        return recommendations
    
    def _get_bot_specific_recommendations(self, bot_name: str, stats: Dict) -> List[Dict]:
        """Получить специфичные рекомендации для бота."""
        
        recommendations = []
        
        if bot_name == "PawnBot":
            if stats['overall_win_rate'] < 0.4:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'STRATEGY',
                    'issue': 'PawnBot may be too focused on pawn structure',
                    'suggestion': 'Balance pawn heuristics with tactical awareness'
                })
        
        elif bot_name == "CriticalBot":
            if stats['avg_think_time'] > 0.5:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'HIERARCHY',
                    'issue': 'Hierarchical delegation may be causing slowdown',
                    'suggestion': 'Cache sub-bot results or reduce delegation frequency'
                })
        
        elif bot_name == "KingValueBot":
            if stats['overall_win_rate'] < 0.4:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'HEATMAPS',
                    'issue': 'Heatmap analysis may not be providing enough value',
                    'suggestion': 'Optimize heatmap patterns or reduce heatmap weight in evaluation'
                })
        
        elif bot_name == "DynamicBot":
            if stats['avg_think_time'] > 2.0:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'ENSEMBLE',
                    'issue': 'Multi-bot ensemble is causing slowdown',
                    'suggestion': 'Reduce number of active bots or implement parallel evaluation'
                })
        
        return recommendations
    
    def create_performance_dashboard(self, bot_stats: Dict, recommendations: Dict):
        """Создать дашборд производительности."""
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Chess AI Performance Dashboard', fontsize=16)
        
        # 1. Win Rate Comparison
        win_rates = [stats['overall_win_rate'] for stats in bot_stats.values()]
        bot_names = list(bot_stats.keys())
        
        axes[0,0].bar(bot_names, win_rates, color='skyblue')
        axes[0,0].set_title('Overall Win Rates')
        axes[0,0].set_ylabel('Win Rate')
        axes[0,0].tick_params(axis='x', rotation=45)
        
        # 2. Performance vs Speed
        think_times = [stats['avg_think_time'] for stats in bot_stats.values()]
        scatter = axes[0,1].scatter(think_times, win_rates, 
                                   s=100, c=range(len(bot_names)), cmap='viridis')
        axes[0,1].set_title('Performance vs Speed')
        axes[0,1].set_xlabel('Average Think Time (s)')
        axes[0,1].set_ylabel('Win Rate')
        
        # Add bot names to scatter plot
        for i, name in enumerate(bot_names):
            axes[0,1].annotate(name, (think_times[i], win_rates[i]), 
                             xytext=(5, 5), textcoords='offset points')
        
        # 3. Performance Trends
        for bot_name, stats in bot_stats.items():
            if len(stats['performance_history']) > 1:
                history = stats['performance_history']
                timestamps = list(range(len(history)))
                win_rates = [h['win_rate'] for h in history]
                axes[1,0].plot(timestamps, win_rates, marker='o', label=bot_name)
        
        axes[1,0].set_title('Performance Trends Over Time')
        axes[1,0].set_xlabel('Tournament Number')
        axes[1,0].set_ylabel('Win Rate')
        axes[1,0].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # 4. Recommendations Priority
        priority_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        for bot_recs in recommendations.values():
            for rec in bot_recs:
                priority_counts[rec['priority']] += 1
        
        axes[1,1].bar(priority_counts.keys(), priority_counts.values(), 
                     color=['red', 'orange', 'green'])
        axes[1,1].set_title('Recommendations by Priority')
        axes[1,1].set_ylabel('Count')
        
        plt.tight_layout()
        plt.savefig('performance_dashboard.png', dpi=300, bbox_inches='tight')
        logger.info("Performance dashboard saved to performance_dashboard.png")
    
    def generate_improvement_plan(self, bot_stats: Dict, recommendations: Dict) -> Dict:
        """Сгенерировать план улучшения."""
        
        plan = {
            'immediate_actions': [],
            'short_term_goals': [],
            'long_term_objectives': []
        }
        
        # Collect all recommendations by priority
        high_priority = []
        medium_priority = []
        low_priority = []
        
        for bot_name, bot_recs in recommendations.items():
            for rec in bot_recs:
                rec_item = {**rec, 'bot': bot_name}
                if rec['priority'] == 'HIGH':
                    high_priority.append(rec_item)
                elif rec['priority'] == 'MEDIUM':
                    medium_priority.append(rec_item)
                else:
                    low_priority.append(rec_item)
        
        # Immediate actions (high priority)
        plan['immediate_actions'] = high_priority[:5]  # Top 5 urgent issues
        
        # Short term goals (medium priority + remaining high)
        plan['short_term_goals'] = medium_priority[:8] + high_priority[5:]
        
        # Long term objectives (low priority + optimization)
        plan['long_term_objectives'] = low_priority + [
            {
                'priority': 'LOW',
                'category': 'OPTIMIZATION',
                'issue': 'General system optimization',
                'suggestion': 'Implement parallel evaluation and advanced caching'
            }
        ]
        
        return plan

def main():
    """Основная функция анализа метрик."""
    
    print("📊 Metrics-Driven Bot Improvement Analysis")
    print("=" * 50)
    
    analyzer = MetricsAnalyzer()
    
    # Load tournament results
    print("📂 Loading tournament results...")
    results = analyzer.load_tournament_results()
    
    if not results:
        print("❌ No tournament results found. Run a tournament first!")
        return
    
    # Analyze performance
    print("🔍 Analyzing bot performance...")
    bot_stats = analyzer.analyze_bot_performance(results)
    
    # Generate recommendations
    print("💡 Generating improvement recommendations...")
    recommendations = analyzer.generate_improvement_recommendations(bot_stats)
    
    # Create dashboard
    print("📈 Creating performance dashboard...")
    analyzer.create_performance_dashboard(bot_stats, recommendations)
    
    # Generate improvement plan
    improvement_plan = analyzer.generate_improvement_plan(bot_stats, recommendations)
    
    # Print summary
    print("\n📋 Performance Summary:")
    print("-" * 30)
    for bot_name, stats in bot_stats.items():
        print(f"{bot_name:15}: {stats['overall_win_rate']:.1%} win rate, "
              f"{stats['avg_think_time']:.2f}s avg time, "
              f"trend: {stats['trend']:+.1%}")
    
    print("\n🚨 Top Priority Issues:")
    print("-" * 30)
    for action in improvement_plan['immediate_actions']:
        print(f"🔴 {action['bot']}: {action['issue']}")
        print(f"   💡 {action['suggestion']}\n")
    
    # Save results
    output = {
        'analysis_date': datetime.now().isoformat(),
        'bot_stats': bot_stats,
        'recommendations': recommendations,
        'improvement_plan': improvement_plan
    }
    
    with open('metrics_analysis_results.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print("💾 Detailed analysis saved to metrics_analysis_results.json")

if __name__ == "__main__":
    main()
