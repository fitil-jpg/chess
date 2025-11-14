#!/usr/bin/env python3
"""
Візуалізація результатів аналізу ефективності ботів
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from basic_tournament_analysis import TournamentAnalyzer
import os

def create_effectiveness_charts():
    """Створення візуалізацій ефективності ботів"""
    analyzer = TournamentAnalyzer()
    analyzer.load_latest_results()
    df = analyzer.analyze_bot_effectiveness()
    
    # Створення директорії для графіків
    os.makedirs('analysis/charts', exist_ok=True)
    
    # 1. Графік ефективності в матчах
    plt.figure(figsize=(12, 8))
    
    # Створення subplot'ів
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Аналіз ефективності шахових ботів', fontsize=16, fontweight='bold')
    
    # 1. Ефективність у матчах
    bars1 = ax1.bar(df['Bot'], df['Match_Efficiency_%'], color='skyblue', alpha=0.8)
    ax1.set_title('Ефективність у матчах (%)')
    ax1.set_ylabel('Ефективність %')
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, alpha=0.3)
    
    # Додавання значень на стовпці
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{height:.1f}%', ha='center', va='bottom')
    
    # 2. Ефективність в іграх
    bars2 = ax2.bar(df['Bot'], df['Game_Efficiency_%'], color='lightcoral', alpha=0.8)
    ax2.set_title('Ефективність в окремих іграх (%)')
    ax2.set_ylabel('Ефективність %')
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(True, alpha=0.3)
    
    for bar in bars2:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{height:.1f}%', ha='center', va='bottom')
    
    # 3. Розподіл результатів (перемоги/нічиї/поразки)
    x = np.arange(len(df['Bot']))
    width = 0.25
    
    bars3 = ax3.bar(x - width, df['Match_Wins'], width, label='Перемоги', color='green', alpha=0.8)
    bars4 = ax3.bar(x, df['Match_Draws'], width, label='Нічиї', color='gray', alpha=0.8)
    bars5 = ax3.bar(x + width, df['Match_Losses'], width, label='Поразки', color='red', alpha=0.8)
    
    ax3.set_title('Розподіл результатів у матчах')
    ax3.set_ylabel('Кількість')
    ax3.set_xticks(x)
    ax3.set_xticklabels(df['Bot'], rotation=45)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Порівняння очок
    bars6 = ax4.bar(df['Bot'], df['Total_Match_Points'], color='gold', alpha=0.8)
    ax4.set_title('Загальні очки в турнірі')
    ax4.set_ylabel('Очки')
    ax4.tick_params(axis='x', rotation=45)
    ax4.grid(True, alpha=0.3)
    
    for bar in bars6:
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{int(height)}', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('analysis/charts/bot_effectiveness_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Створення таблиці результатів
    create_summary_table(df)

def create_summary_table(df):
    """Створення детальної таблиці результатів"""
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.axis('tight')
    ax.axis('off')
    
    # Підготовка даних для таблиці
    table_data = []
    for _, row in df.iterrows():
        table_data.append([
            row['Bot'],
            f"{row['Matches_Played']}",
            f"{row['Match_Wins']}-{row['Match_Draws']}-{row['Match_Losses']}",
            f"{row['Match_Efficiency_%']}%",
            f"{row['Games_Played']}",
            f"{row['Game_Wins']}-{row['Game_Draws']}-{row['Game_Losses']}",
            f"{row['Game_Efficiency_%']}%",
            f"{int(row['Total_Match_Points'])}"
        ])
    
    # Створення таблиці
    table = ax.table(cellText=table_data,
                    colLabels=['Бот', 'Матчі', 'Результати', 'Ефективність%', 'Ігри', 'Результати', 'Ефективність%', 'Очки'],
                    cellLoc='center',
                    loc='center',
                    colWidths=[0.15, 0.08, 0.15, 0.1, 0.08, 0.15, 0.1, 0.08])
    
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    
    # Стилізація заголовків
    for i in range(len(table_data[0])):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Виділення кольором найкращих результатів
    max_efficiency_idx = df['Match_Efficiency_%'].idxmax()
    max_points_idx = df['Total_Match_Points'].idxmax()
    
    for i in range(len(table_data)):
        if i == max_efficiency_idx:
            table[(i+1, 3)].set_facecolor('#90EE90')  # Світло-зелений для найвищої ефективності
        if i == max_points_idx:
            table[(i+1, 7)].set_facecolor('#FFD700')  # Золотий для найбільше очок
    
    plt.title('Детальна таблиця результатів турніру', fontsize=16, fontweight='bold', pad=20)
    plt.savefig('analysis/charts/detailed_results_table.png', dpi=300, bbox_inches='tight')
    plt.show()

def analyze_draw_patterns():
    """Аналіз патернів нічиїх"""
    analyzer = TournamentAnalyzer()
    analyzer.load_latest_results()
    df = analyzer.analyze_bot_effectiveness()
    
    # Розрахунок відсотка нічиїх
    df['Draw_Percentage_Matches'] = (df['Match_Draws'] / df['Matches_Played']) * 100
    df['Draw_Percentage_Games'] = (df['Game_Draws'] / df['Games_Played']) * 100
    
    plt.figure(figsize=(12, 6))
    
    x = np.arange(len(df['Bot']))
    width = 0.35
    
    bars1 = plt.bar(x - width/2, df['Draw_Percentage_Matches'], width, 
                   label='Нічиї в матчах', color='lightblue', alpha=0.8)
    bars2 = plt.bar(x + width/2, df['Draw_Percentage_Games'], width,
                   label='Нічиї в іграх', color='darkblue', alpha=0.8)
    
    plt.title('Аналіз відсотка нічиїх', fontsize=14, fontweight='bold')
    plt.xlabel('Боти')
    plt.ylabel('Відсоток нічиїх')
    plt.xticks(x, df['Bot'], rotation=45)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Додавання значень
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{height:.1f}%', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('analysis/charts/draw_patterns_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    print("=== СТВОРЕННЯ ВІЗУАЛІЗАЦІЙ ===")
    create_effectiveness_charts()
    analyze_draw_patterns()
    print("Графіки збережено в директорії analysis/charts/")
