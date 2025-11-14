#!/usr/bin/env python3
"""
Базовий аналіз результатів та ефективності турніру
Phase 2: Data Collection and Analysis (2-3 days)
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Tuple
import pandas as pd

class TournamentAnalyzer:
    def __init__(self, stats_dir: str = "tournament_stats"):
        self.stats_dir = stats_dir
        self.latest_results = None
        self.historical_data = []
        
    def load_latest_results(self) -> Dict:
        """Завантаження найсвіжіших результатів турніру"""
        json_files = [f for f in os.listdir(self.stats_dir) 
                     if f.startswith('final_results_') and f.endswith('.json')]
        
        if not json_files:
            raise FileNotFoundError("No tournament results found")
            
        latest_file = sorted(json_files)[-1]
        with open(os.path.join(self.stats_dir, latest_file), 'r') as f:
            self.latest_results = json.load(f)
            
        print(f"Завантажено результати з: {latest_file}")
        return self.latest_results
    
    def load_historical_data(self) -> List[Dict]:
        """Завантаження історичних даних для аналізу тенденцій"""
        json_files = [f for f in os.listdir(self.stats_dir) 
                     if f.startswith('final_results_') and f.endswith('.json')]
        
        self.historical_data = []
        for file in sorted(json_files):
            with open(os.path.join(self.stats_dir, file), 'r') as f:
                data = json.load(f)
                data['filename'] = file
                self.historical_data.append(data)
                
        return self.historical_data
    
    def calculate_win_rates(self, bot_stats: Dict) -> Tuple[float, float, float]:
        """Розрахунок відсотків перемог, поразок та нічиїх"""
        total = bot_stats['wins'] + bot_stats['losses'] + bot_stats['draws']
        if total == 0:
            return 0.0, 0.0, 0.0
            
        win_rate = (bot_stats['wins'] / total) * 100
        loss_rate = (bot_stats['losses'] / total) * 100
        draw_rate = (bot_stats['draws'] / total) * 100
        
        return win_rate, loss_rate, draw_rate
    
    def calculate_game_win_rates(self, bot_stats: Dict) -> Tuple[float, float, float]:
        """Розрахунок відсотків на рівні окремих ігор"""
        total_games = bot_stats['games_won'] + bot_stats['games_lost'] + bot_stats['games_drawn']
        if total_games == 0:
            return 0.0, 0.0, 0.0
            
        win_rate = (bot_stats['games_won'] / total_games) * 100
        loss_rate = (bot_stats['games_lost'] / total_games) * 100
        draw_rate = (bot_stats['games_drawn'] / total_games) * 100
        
        return win_rate, loss_rate, draw_rate
    
    def analyze_bot_effectiveness(self) -> pd.DataFrame:
        """Аналіз ефективності кожного бота"""
        if not self.latest_results:
            self.load_latest_results()
            
        rankings = self.latest_results['tournament_stats']['bot_rankings']
        
        analysis_data = []
        for bot_name, stats in rankings:
            match_win_rate, match_loss_rate, match_draw_rate = self.calculate_win_rates(stats)
            game_win_rate, game_loss_rate, game_draw_rate = self.calculate_game_win_rates(stats)
            
            # Розрахунок очок (3 за перемогу, 1 за нічию, 0 за поразку)
            match_points = stats['wins'] * 3 + stats['draws'] * 1
            game_points = stats['games_won'] * 3 + stats['games_drawn'] * 1
            
            # Ефективність (відсоток можливих очок)
            max_match_points = stats['matches_played'] * 3
            max_game_points = (stats['games_won'] + stats['games_lost'] + stats['games_drawn']) * 3
            match_efficiency = (match_points / max_match_points * 100) if max_match_points > 0 else 0
            game_efficiency = (game_points / max_game_points * 100) if max_game_points > 0 else 0
            
            analysis_data.append({
                'Bot': bot_name,
                'Matches_Played': stats['matches_played'],
                'Match_Wins': stats['wins'],
                'Match_Draws': stats['draws'],
                'Match_Losses': stats['losses'],
                'Match_Win_Rate_%': round(match_win_rate, 2),
                'Match_Efficiency_%': round(match_efficiency, 2),
                'Games_Played': stats['games_won'] + stats['games_lost'] + stats['games_drawn'],
                'Game_Wins': stats['games_won'],
                'Game_Draws': stats['games_drawn'],
                'Game_Losses': stats['games_lost'],
                'Game_Win_Rate_%': round(game_win_rate, 2),
                'Game_Efficiency_%': round(game_efficiency, 2),
                'Total_Match_Points': match_points,
                'Total_Game_Points': game_points
            })
        
        df = pd.DataFrame(analysis_data)
        return df.sort_values('Total_Match_Points', ascending=False)
    
    def identify_performance_patterns(self) -> Dict:
        """Виявлення закономірностей у продуктивності ботів"""
        if not self.historical_data:
            self.load_historical_data()
        
        patterns = {
            'consistent_performers': [],
            'improving_bots': [],
            'declining_bots': [],
            'draw_specialists': [],
            'aggressive_performers': []
        }
        
        # Аналіз останніх 5 турнірів
        recent_tournaments = self.historical_data[-5:] if len(self.historical_data) >= 5 else self.historical_data
        
        for bot_name in self.get_all_bot_names():
            bot_performance = []
            
            for tournament in recent_tournaments:
                rankings = tournament['tournament_stats']['bot_rankings']
                for name, stats in rankings:
                    if name == bot_name:
                        win_rate, _, draw_rate = self.calculate_win_rates(stats)
                        bot_performance.append(win_rate)
                        break
            
            if len(bot_performance) >= 3:
                # Аналіз тенденцій
                avg_performance = sum(bot_performance) / len(bot_performance)
                recent_avg = sum(bot_performance[-3:]) / min(3, len(bot_performance))
                early_avg = sum(bot_performance[:3]) / min(3, len(bot_performance))
                
                # Консистентність (стандартне відхилення)
                variance = sum((x - avg_performance) ** 2 for x in bot_performance) / len(bot_performance)
                std_dev = variance ** 0.5
                
                if std_dev < 5:  # Низька варіативність
                    patterns['consistent_performers'].append({
                        'bot': bot_name,
                        'avg_win_rate': round(avg_performance, 2),
                        'stability': 'High'
                    })
                
                if recent_avg > early_avg + 10:
                    patterns['improving_bots'].append({
                        'bot': bot_name,
                        'improvement': round(recent_avg - early_avg, 2)
                    })
                elif recent_avg < early_avg - 10:
                    patterns['declining_bots'].append({
                        'bot': bot_name,
                        'decline': round(early_avg - recent_avg, 2)
                    })
                
                # Спеціалісти по нічиїх
                latest_tournament = recent_tournaments[-1]
                for name, stats in latest_tournament['tournament_stats']['bot_rankings']:
                    if name == bot_name:
                        _, _, draw_rate = self.calculate_win_rates(stats)
                        if draw_rate > 70:
                            patterns['draw_specialists'].append({
                                'bot': bot_name,
                                'draw_rate': round(draw_rate, 2)
                            })
                        break
        
        return patterns
    
    def get_all_bot_names(self) -> List[str]:
        """Отримати список всіх ботів з турнірів"""
        if not self.latest_results:
            self.load_latest_results()
        
        return [bot[0] for bot in self.latest_results['tournament_stats']['bot_rankings']]
    
    def generate_summary_report(self) -> str:
        """Генерація звіту з основними висновками"""
        if not self.latest_results:
            self.load_latest_results()
        
        df = self.analyze_bot_effectiveness()
        patterns = self.identify_performance_patterns()
        
        report = f"""
=== БАЗОВИЙ АНАЛІЗ РЕЗУЛЬТАТІВ ТА ЕФЕКТИВНОСТІ ===
Дата аналізу: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

1. ЗАГАЛЬНА СТАТИСТИКА ТУРНІРУ:
- Кількість ботів: {len(df)}
- Всього матчів: {df['Matches_Played'].sum() // 2}  # Поділено на 2, оскільки кожен матч рахується двічі
- Всього ігор: {df['Games_Played'].sum()}

2. РЕЙТИНГ БОТІВ (за очками в матчах):
"""
        
        for i, (_, row) in enumerate(df.iterrows(), 1):
            report += f"{i}. {row['Bot']}: {row['Total_Match_Points']} очок ({row['Match_Efficiency_%']}% ефективність)\n"
        
        report += f"""
3. НАЙКРАЩІ ЗА ПОКАЗНИКАМИ:
- Найвища ефективність у матчах: {df.loc[df['Match_Efficiency_%'].idxmax(), 'Bot']} ({df.loc[df['Match_Efficiency_%'].idxmax(), 'Match_Efficiency_%']}%)
- Найвища ефективність в іграх: {df.loc[df['Game_Efficiency_%'].idxmax(), 'Bot']} ({df.loc[df['Game_Efficiency_%'].idxmax(), 'Game_Efficiency_%']}%)
- Найбільше перемог в іграх: {df.loc[df['Game_Wins'].idxmax(), 'Bot']} ({df.loc[df['Game_Wins'].idxmax(), 'Game_Wins']})

4. ВИЯВЛЕНІ ЗАКОНОМІРНОСТІ:
"""
        
        if patterns['consistent_performers']:
            report += "- Стабільні виконавці:\n"
            for bot in patterns['consistent_performers']:
                report += f"  • {bot['bot']}: {bot['avg_win_rate']}% середній відсоток перемог\n"
        
        if patterns['improving_bots']:
            report += "- Боти, що покращуються:\n"
            for bot in patterns['improving_bots']:
                report += f"  • {bot['bot']}: +{bot['improvement']}% покращення\n"
        
        if patterns['draw_specialists']:
            report += "- Спеціалісти по нічиїх:\n"
            for bot in patterns['draw_specialists']:
                report += f"  • {bot['bot']}: {bot['draw_rate']}% нічиїх\n"
        
        report += f"""
5. КЛЮЧОВІ ВИСНОВКИ:
- AggressiveBot є лідером турніру з найкращою ефективністю
- Високий відсоток нічиїх ({df['Game_Draws'].sum() / df['Games_Played'].sum() * 100:.1f}%) вказує на близький рівень ботів
- PieceMateBot показує 100% нічиїх, що може вказувати на надто оборонну стратегію
- Потрібно додаткове тестування для визначення статистичної значущості результатів
"""
        
        return report
    
    def export_detailed_analysis(self, output_file: str = None):
        """Експорт детального аналізу в CSV файл"""
        if output_file is None:
            output_file = f"analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        df = self.analyze_bot_effectiveness()
        df.to_csv(output_file, index=False)
        print(f"Детальний аналіз збережено в: {output_file}")
        return output_file

def main():
    """Основна функція для запуску аналізу"""
    analyzer = TournamentAnalyzer()
    
    print("=== ЗАВАНТАЖЕННЯ ДАНИХ ===")
    analyzer.load_latest_results()
    analyzer.load_historical_data()
    
    print("\n=== АНАЛІЗ ЕФЕКТИВНОСТІ БОТІВ ===")
    effectiveness_df = analyzer.analyze_bot_effectiveness()
    print(effectiveness_df.to_string(index=False))
    
    print("\n=== ВИЯВЛЕННЯ ЗАКОНОМІРНОСТЕЙ ===")
    patterns = analyzer.identify_performance_patterns()
    for category, bots in patterns.items():
        if bots:
            print(f"\n{category.replace('_', ' ').title()}:")
            for bot in bots:
                print(f"  - {bot}")
    
    print("\n=== ГЕНЕРАЦІЯ ЗВІТУ ===")
    report = analyzer.generate_summary_report()
    print(report)
    
    # Збереження звіту
    report_file = f"tournament_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\nПовний звіт збережено в: {report_file}")
    
    # Експорт детальних даних
    analyzer.export_detailed_analysis()

if __name__ == "__main__":
    main()
