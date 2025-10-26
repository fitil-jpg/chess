#!/usr/bin/env python3
"""
Скрипт для запуска турнирного паттерн-вьювера
"""

import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tournament_pattern_viewer import main

if __name__ == "__main__":
    main()