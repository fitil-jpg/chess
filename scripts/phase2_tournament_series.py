#!/usr/bin/env python3
"""
Phase 2 Tournament Series: Comprehensive testing with different time controls
and detailed strategy analysis.

Runs tournaments with multiple time controls and generates comprehensive reports.
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple

# Add project root to path
SCRIPT_DIR = os.path.dirname(__file__)
ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Import after path setup
try:
    from analysis.basic_tournament_analysis import TournamentAnalyzer
except ImportError:
    # Fallback if analysis module not available
    TournamentAnalyzer = None

class Phase2TournamentSeries:
    """Comprehensive tournament series for Phase 2 analysis."""
    
    def __init__(self):
        self.time_controls = [
            {"name": "Blitz", "time": 30, "description": "30 секунд на гру"},
            {"name": "Rapid", "time": 60, "description": "1 хвилина на гру"},
            {"name": "Standard", "time": 180, "description": "3 хвилини на гру"},
            {"name": "Classical", "time": 300, "description": "5 хвилин на гру"}
        ]
        
        self.bot_list = ["AggressiveBot", "EndgameBot", "FortifyBot", "DynamicBot", "PieceMateBot"]
        self.results = {}
        
    def run_single_tournament(self, time_control: Dict) -> Dict:
        """Запустити один турнір з вказаним часовим контролем."""
        print(f"\n🏁 Запуск турніру: {time_control['name']} ({time_control['description']})")
        
        # Формуємо команду
        cmd = [
            sys.executable, "scripts/tournament.py",
            "--agents", ",".join(self.bot_list),
            "--bo", "3",
            "--time", str(time_control["time"])
        ]
        
        start_time = time.time()
        
        try:
            # Запускаємо турнір
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)  # 2 години таймаут
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                print(f"✅ Турнір {time_control['name']} завершено за {execution_time/60:.1f} хв")
                
                # Аналізуємо результати
                if TournamentAnalyzer:
                    analyzer = TournamentAnalyzer()
                    try:
                        analyzer.load_latest_results()
                        df = analyzer.analyze_bot_effectiveness()
                        
                        return {
                            "time_control": time_control,
                            "execution_time_minutes": execution_time / 60,
                            "results": df.to_dict('records'),
                            "timestamp": datetime.now().isoformat()
                        }
                    except Exception as e:
                        print(f"⚠️ Помилка аналізу результатів: {e}")
                        return {"error": str(e)}
                else:
                    # Simple fallback without detailed analysis
                    return {
                        "time_control": time_control,
                        "execution_time_minutes": execution_time / 60,
                        "results": [],
                        "timestamp": datetime.now().isoformat(),
                        "note": "Analysis module not available"
                    }
            else:
                print(f"❌ Помилка в турнірі {time_control['name']}: {result.stderr}")
                return {"error": result.stderr}
                
        except subprocess.TimeoutExpired:
            print(f"⏰ Турнір {time_control['name']} перевищив час виконання")
            return {"error": "Timeout"}
        except Exception as e:
            print(f"❌ Критична помилка в турнірі {time_control['name']}: {e}")
            return {"error": str(e)}
    
    def run_all_tournaments(self) -> Dict:
        """Запустити всі турніри серії."""
        print("🚀 Початок серії турнірів Phase 2")
        print(f"📋 План: {len(self.time_controls)} турнірів з {len(self.bot_list)} ботами")
        
        all_results = {}
        
        for i, time_control in enumerate(self.time_controls, 1):
            print(f"\n{'='*60}")
            print(f"Турнір {i}/{len(self.time_controls)}: {time_control['name']}")
            print(f"{'='*60}")
            
            result = self.run_single_tournament(time_control)
            all_results[time_control['name']] = result
            
            # Невелика пауза між турнірами
            if i < len(self.time_controls):
                print("⏸️ Пауза 30 секунд між турнірами...")
                time.sleep(30)
        
        return all_results
    
    def generate_comprehensive_report(self, results: Dict) -> str:
        """Згенерувати комплексний звіт по всіх турнірах."""
        report = f"""
=== PHASE 2 КОМПЛЕКСНИЙ ЗВІТ ТУРНІРНОЇ СЕРІЇ ===
Дата генерації: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

1. ОГЛЯД ТУРНІРІВ:
"""
        
        total_time = 0
        successful_tournaments = 0
        
        for name, result in results.items():
            if "error" not in result:
                execution_time = result.get("execution_time_minutes", 0)
                total_time += execution_time
                successful_tournaments += 1
                
                report += f"   ✅ {name}: {execution_time:.1f} хв\n"
            else:
                report += f"   ❌ {name}: Помилка - {result['error']}\n"
        
        report += f"\n   Загальний час виконання: {total_time:.1f} хв\n"
        report += f"   Успішних турнірів: {successful_tournaments}/{len(self.time_controls)}\n\n"
        
        # Аналіз ефективності по таймінгах
        report += "2. АНАЛІЗ ЕФЕКТИВНОСТІ ЗА ЧАСОВИМИ КОНТРОЛЯМИ:\n\n"
        
        bot_performance = {}
        
        for name, result in results.items():
            if "error" not in result and "results" in result:
                report += f"   {name} ({result['time_control']['description']}):\n"
                
                for bot_result in result["results"]:
                    bot_name = bot_result["Bot"]
                    if bot_name not in bot_performance:
                        bot_performance[bot_name] = {}
                    
                    bot_performance[bot_name][name] = {
                        "efficiency": bot_result["Match_Efficiency_%"],
                        "win_rate": bot_result["Match_Win_Rate_%"],
                        "points": bot_result["Total_Match_Points"]
                    }
                    
                    report += f"     • {bot_name}: {bot_result['Total_Match_Points']} очок, "
                    report += f"{bot_result['Match_Efficiency_%']}% ефективність\n"
                report += "\n"
        
        # Тенденції по таймінгах
        report += "3. ТЕНДЕНЦІЇ ТА ВИЯВЛЕНІ ЗАКОНОМІРНОСТІ:\n\n"
        
        for bot_name in bot_performance.keys():
            report += f"   {bot_name}:\n"
            
            efficiencies = []
            for time_name in ["Blitz", "Rapid", "Standard", "Classical"]:
                if time_name in bot_performance[bot_name]:
                    eff = bot_performance[bot_name][time_name]["efficiency"]
                    efficiencies.append(eff)
                    report += f"     • {time_name}: {eff}% ефективність\n"
            
            if len(efficiencies) >= 2:
                trend = "стабільна" if max(efficiencies) - min(efficiencies) < 10 else "нестабільна"
                if len(efficiencies) >= 3:
                    if efficiencies[-1] > efficiencies[0]:
                        trend += " (покращення з часом)"
                    elif efficiencies[-1] < efficiencies[0]:
                        trend += " (погіршення з часом)"
                
                report += f"     • Тенденція: {trend}\n"
            report += "\n"
        
        # Рекомендації
        report += "4. РЕКОМЕНДАЦІЇ ДЛЯ ОПТИМІЗАЦІЇ:\n\n"
        
        # Аналізуємо найкращі/найгірші таймінги для кожного бота
        for bot_name in bot_performance.keys():
            if len(bot_performance[bot_name]) >= 2:
                best_time = max(bot_performance[bot_name].items(), 
                              key=lambda x: x[1]["efficiency"])
                worst_time = min(bot_performance[bot_name].items(), 
                               key=lambda x: x[1]["efficiency"])
                
                report += f"   • {bot_name}: Найкращий таймінг - {best_time[0]} "
                report += f"({best_time[1]['efficiency']}%), "
                report += f"Найгірший - {worst_time[0]} ({worst_time[1]['efficiency']}%)\n"
        
        report += "\n   • Загальні рекомендації:\n"
        report += "     - Тестувати ботів з їх оптимальними таймінгами\n"
        report += "     - Розглянути адаптивні стратегії для різних фаз гри\n"
        report += "     - Оптимізувати алгоритми для бліц-контролю\n"
        report += "     - Поглибити аналіз ендшпілю для довгих партій\n\n"
        
        # Статистичний аналіз
        report += "5. СТАТИСТИЧНИЙ АНАЛІЗ:\n\n"
        
        if successful_tournaments >= 2:
            report += "   • Стабільність рейтингів: "
            # Простий аналіз стабільності
            all_efficiencies = []
            for bot_data in bot_performance.values():
                all_efficiencies.extend([perf["efficiency"] for perf in bot_data.values()])
            
            if all_efficiencies:
                variance = sum((x - sum(all_efficiencies)/len(all_efficiencies))**2 
                             for x in all_efficiencies) / len(all_efficiencies)
                std_dev = variance ** 0.5
                
                if std_dev < 15:
                    report += "Висока\n"
                elif std_dev < 25:
                    report += "Середня\n"
                else:
                    report += "Низька\n"
        
        report += f"\n=== КІНЕЦЬ ЗВІТУ ===\n"
        
        return report
    
    def save_comprehensive_report(self, report: str, results: Dict):
        """Зберегти комплексний звіт та дані."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Зберігаємо текстовий звіт
        report_file = f"tournament_stats/phase2_comprehensive_report_{timestamp}.txt"
        os.makedirs("tournament_stats", exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Зберігаємо JSON дані
        data_file = f"tournament_stats/phase2_tournament_data_{timestamp}.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 Комплексний звіт збережено: {report_file}")
        print(f"💾 Дані турнірів збережено: {data_file}")
        
        return report_file, data_file

def main():
    """Основна функція для запуску серії турнірів."""
    series = Phase2TournamentSeries()
    
    print("🎯 Phase 2 Tournament Series")
    print("📝 Опис: Комплексне тестування з різними часовими контролями")
    print("⏱️  Таймінги: Blitz (30с), Rapid (1хв), Standard (3хв), Classical (5хв)")
    print("🤖 Боти: " + ", ".join(series.bot_list))
    
    # Запитання підтвердження
    response = input("\n❓ Почати серію турнірів? (y/N): ").strip().lower()
    if response not in ['y', 'yes', 'так']:
        print("❌ Скасовано користувачем")
        return
    
    try:
        # Запускаємо всі турніри
        results = series.run_all_tournaments()
        
        # Генеруємо звіт
        print("\n📊 Генерація комплексного звіту...")
        report = series.generate_comprehensive_report(results)
        
        # Зберігаємо результати
        report_file, data_file = series.save_comprehensive_report(report, results)
        
        print("\n✅ Серію турнірів Phase 2 завершено!")
        print(f"📄 Звіт: {report_file}")
        print(f"💾 Дані: {data_file}")
        
        # Показуємо короткий звіт
        print("\n" + "="*60)
        print(report[:1000] + "\n..." if len(report) > 1000 else report)
        
    except KeyboardInterrupt:
        print("\n⏹️  Серію турнірів перервано користувачем")
    except Exception as e:
        print(f"\n❌ Критична помилка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
