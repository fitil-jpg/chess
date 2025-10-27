#!/usr/bin/env python3
import sys
import logging
from chess_ai.pattern_manager import PatternManager

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

if __name__ == '__main__':
    pm = PatternManager()
    stats = pm.get_pattern_statistics()
    print({k: stats[k] for k in ('total_patterns',) if k in stats})
    # Print a few sample ids and moves
    count = 0
    for pid, pat in pm.patterns.items():
        print(f"ID={pid[:8]} move={pat.move} types={','.join(pat.pattern_types)}")
        count += 1
        if count >= 5:
            break
