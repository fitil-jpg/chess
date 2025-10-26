# Структура JSON файла паттерна

## Что отображается в JSON файле паттерна:

### 1. **Основная информация**
```json
{
  "pattern_id": "abc123def456",
  "name": "Королевская вилка",
  "description": "Конь атакует короля и ферзя одновременно",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "author": "PatternDetector_v1.0"
}
```

### 2. **Позиция и ход**
```json
{
  "position": {
    "fen_before": "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R b KQkq - 0 4",
    "fen_after": "r1bqkb1r/pppp1ppp/2n5/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 1 5",
    "key_move": {
      "san": "Nxd4",
      "uci": "c6d4",
      "from_square": "c6",
      "to_square": "d4"
    }
  }
}
```

### 3. **Участвующие фигуры (только те, что влияют на паттерн)**
```json
{
  "participating_pieces": {
    "primary_pieces": [
      {
        "square": "c6",
        "piece": "n",
        "role": "attacker",
        "influence": 1.0
      },
      {
        "square": "e8",
        "piece": "k", 
        "role": "target",
        "influence": 0.8
      },
      {
        "square": "d8",
        "piece": "q",
        "role": "target",
        "influence": 0.9
      }
    ],
    "supporting_pieces": [
      {
        "square": "f3",
        "piece": "N",
        "role": "defender",
        "influence": 0.6
      }
    ],
    "excluded_pieces": [
      "a8", "b8", "f8", "g8", "h8", "a7", "b7", "c7", "d7", "e7", "f7", "g7", "h7"
    ]
  }
}
```

### 4. **Категоризация и теги**
```json
{
  "categories": {
    "primary": "tactical",
    "secondary": ["fork", "knight_pattern", "royal_fork"],
    "game_phase": "middlegame",
    "complexity": "intermediate"
  },
  "tags": ["вилка", "конь", "король", "ферзь", "тактика"],
  "difficulty_rating": 7.5
}
```

### 5. **Анализ альтернатив**
```json
{
  "alternatives": {
    "considered_moves": [
      {
        "move": "Ne7+",
        "evaluation": 0.3,
        "reason": "Шах, но менее эффективно"
      },
      {
        "move": "Nd5",
        "evaluation": 0.1,
        "reason": "Централизация, но без тактики"
      }
    ],
    "best_defense": {
      "move": "Qd7",
      "evaluation": -0.5,
      "reason": "Защита ферзя"
    }
  }
}
```

### 6. **Контекст игры**
```json
{
  "game_context": {
    "move_number": 5,
    "turn": "black",
    "material_balance": 0,
    "castling_rights": "KQkq",
    "game_phase": "opening_to_middlegame",
    "time_pressure": false,
    "evaluation_before": 0.2,
    "evaluation_after": -1.5,
    "evaluation_swing": -1.7
  }
}
```

### 7. **Размены (если применимо)**
```json
{
  "exchange_sequence": {
    "is_exchange": true,
    "moves_ahead": 3,
    "sequence": [
      {
        "move": "Nxd4",
        "capture": "d4_pawn",
        "material_change": +1
      },
      {
        "move": "Qxd4",
        "capture": "d4_knight", 
        "material_change": -3
      },
      {
        "move": "Bxf7+",
        "capture": "f7_pawn",
        "material_change": +1,
        "special": "discovered_check"
      }
    ],
    "net_material": -1,
    "positional_gain": 2.5,
    "total_evaluation": +1.5
  }
}
```

### 8. **Визуализация**
```json
{
  "visualization": {
    "highlighted_squares": ["c6", "d4", "e8", "d8"],
    "arrows": [
      {
        "from": "c6",
        "to": "d4",
        "color": "red",
        "type": "attack"
      },
      {
        "from": "d4", 
        "to": "e8",
        "color": "red",
        "type": "threat"
      },
      {
        "from": "d4",
        "to": "d8", 
        "color": "red",
        "type": "threat"
      }
    ],
    "heatmap_data": {
      "d4": 1.0,
      "e8": 0.8,
      "d8": 0.9,
      "c6": 0.7
    }
  }
}
```

### 9. **Метаданные**
```json
{
  "metadata": {
    "detection_confidence": 0.95,
    "pattern_frequency": "common",
    "learning_value": 8.5,
    "bot_evaluations": {
      "StockfishBot": {
        "confidence": 0.9,
        "evaluation": -1.5,
        "depth": 15
      },
      "DynamicBot": {
        "confidence": 0.8,
        "evaluation": -1.3,
        "preferred_move": "Nxd4"
      }
    },
    "human_annotations": {
      "verified": true,
      "verified_by": "user",
      "notes": "Классическая королевская вилка"
    }
  }
}
```

### 10. **Связанные паттерны**
```json
{
  "related_patterns": {
    "similar_patterns": ["knight_fork_basic", "royal_fork_variation_2"],
    "counter_patterns": ["fork_defense_qd7", "fork_prevention_h6"],
    "follow_up_patterns": ["material_advantage_conversion"]
  }
}
```

## Полный пример JSON файла:

Файл: `patterns/royal_fork_abc123def456.json`

```json
{
  "pattern_id": "abc123def456",
  "name": "Королевская вилка конём",
  "description": "Конь с d4 атакует короля на e8 и ферзя на d8 одновременно",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "author": "PatternDetector_v1.0",
  
  "position": {
    "fen_before": "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R b KQkq - 0 4",
    "fen_after": "r1bqkb1r/pppp1ppp/2n5/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 1 5",
    "key_move": {
      "san": "Nxd4", 
      "uci": "c6d4",
      "from_square": "c6",
      "to_square": "d4"
    }
  },
  
  "participating_pieces": {
    "primary_pieces": [
      {"square": "c6", "piece": "n", "role": "attacker", "influence": 1.0},
      {"square": "e8", "piece": "k", "role": "target", "influence": 0.8},
      {"square": "d8", "piece": "q", "role": "target", "influence": 0.9}
    ],
    "supporting_pieces": [
      {"square": "f3", "piece": "N", "role": "defender", "influence": 0.6}
    ],
    "excluded_pieces": ["a8", "b8", "f8", "g8", "h8", "a7", "b7", "c7", "d7", "e7", "f7", "g7", "h7"]
  },
  
  "categories": {
    "primary": "tactical",
    "secondary": ["fork", "knight_pattern", "royal_fork"],
    "game_phase": "middlegame", 
    "complexity": "intermediate"
  },
  "tags": ["вилка", "конь", "король", "ферзь", "тактика"],
  "difficulty_rating": 7.5,
  
  "alternatives": {
    "considered_moves": [
      {"move": "Ne7+", "evaluation": 0.3, "reason": "Шах, но менее эффективно"},
      {"move": "Nd5", "evaluation": 0.1, "reason": "Централизация, но без тактики"}
    ],
    "best_defense": {"move": "Qd7", "evaluation": -0.5, "reason": "Защита ферзя"}
  },
  
  "game_context": {
    "move_number": 5,
    "turn": "black",
    "material_balance": 0,
    "castling_rights": "KQkq",
    "game_phase": "opening_to_middlegame",
    "evaluation_swing": -1.7
  },
  
  "exchange_sequence": null,
  
  "visualization": {
    "highlighted_squares": ["c6", "d4", "e8", "d8"],
    "arrows": [
      {"from": "c6", "to": "d4", "color": "red", "type": "attack"},
      {"from": "d4", "to": "e8", "color": "red", "type": "threat"},
      {"from": "d4", "to": "d8", "color": "red", "type": "threat"}
    ],
    "heatmap_data": {"d4": 1.0, "e8": 0.8, "d8": 0.9, "c6": 0.7}
  },
  
  "metadata": {
    "detection_confidence": 0.95,
    "pattern_frequency": "common",
    "learning_value": 8.5,
    "bot_evaluations": {
      "StockfishBot": {"confidence": 0.9, "evaluation": -1.5, "depth": 15}
    },
    "human_annotations": {
      "verified": true,
      "notes": "Классическая королевская вилка"
    }
  },
  
  "related_patterns": {
    "similar_patterns": ["knight_fork_basic"],
    "counter_patterns": ["fork_defense_qd7"]
  }
}
```

Эта структура позволяет:
- **Точно определить участвующие фигуры**
- **Исключить неучаствующие фигуры**  
- **Анализировать размены на несколько ходов вперёд**
- **Хранить визуализацию и метаданные**
- **Связывать похожие паттерны**