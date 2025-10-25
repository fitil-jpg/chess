"""
Pattern storage and cataloging system for chess patterns.
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from chess_ai.pattern_detector import ChessPattern, PatternType

logger = logging.getLogger(__name__)


class PatternCatalog:
    """Manages storage and retrieval of chess patterns"""
    
    def __init__(self, catalog_path: str = "patterns/catalog.json"):
        self.catalog_path = Path(catalog_path)
        self.patterns: List[ChessPattern] = []
        self._ensure_directory()
        
    def _ensure_directory(self):
        """Ensure the patterns directory exists"""
        self.catalog_path.parent.mkdir(parents=True, exist_ok=True)
        
    def load_patterns(self) -> List[ChessPattern]:
        """Load patterns from catalog file"""
        if not self.catalog_path.exists():
            logger.info(f"No catalog found at {self.catalog_path}")
            return []
            
        try:
            with open(self.catalog_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.patterns = [ChessPattern.from_dict(p) for p in data.get("patterns", [])]
            logger.info(f"Loaded {len(self.patterns)} patterns from catalog")
            return self.patterns
            
        except Exception as e:
            logger.error(f"Failed to load patterns: {e}")
            return []
    
    def save_patterns(self, patterns: List[ChessPattern] = None):
        """Save patterns to catalog file"""
        if patterns is not None:
            self.patterns = patterns
            
        try:
            data = {
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "count": len(self.patterns),
                "patterns": [p.to_dict() for p in self.patterns]
            }
            
            with open(self.catalog_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Saved {len(self.patterns)} patterns to catalog")
            
        except Exception as e:
            logger.error(f"Failed to save patterns: {e}")
    
    def add_pattern(self, pattern: ChessPattern):
        """Add a new pattern to the catalog"""
        # Add timestamp to metadata
        pattern.metadata["added_at"] = datetime.now().isoformat()
        self.patterns.append(pattern)
        
    def add_patterns(self, patterns: List[ChessPattern]):
        """Add multiple patterns to the catalog"""
        for pattern in patterns:
            self.add_pattern(pattern)
    
    def get_patterns(
        self,
        pattern_types: List[str] = None,
        min_eval_change: float = None,
        opening_only: bool = False,
        endgame_only: bool = False
    ) -> List[ChessPattern]:
        """
        Get patterns with optional filtering.
        
        Args:
            pattern_types: Filter by pattern types
            min_eval_change: Minimum evaluation change
            opening_only: Only opening patterns (moves 1-10)
            endgame_only: Only endgame patterns
            
        Returns:
            Filtered list of patterns
        """
        filtered = self.patterns
        
        if pattern_types:
            filtered = [
                p for p in filtered
                if any(pt in p.pattern_types for pt in pattern_types)
            ]
        
        if min_eval_change is not None:
            filtered = [
                p for p in filtered
                if abs(p.evaluation.get("change", 0)) >= min_eval_change
            ]
        
        if opening_only:
            filtered = [
                p for p in filtered
                if p.metadata.get("fullmove_number", 100) <= 10
            ]
        
        if endgame_only:
            filtered = [
                p for p in filtered
                if PatternType.ENDGAME_TECHNIQUE in p.pattern_types
            ]
        
        return filtered
    
    def remove_pattern(self, index: int):
        """Remove a pattern by index"""
        if 0 <= index < len(self.patterns):
            del self.patterns[index]
    
    def clear_patterns(self):
        """Clear all patterns"""
        self.patterns.clear()
    
    def export_to_pgn(self, output_path: str, patterns: List[ChessPattern] = None):
        """Export patterns to PGN format for analysis"""
        if patterns is None:
            patterns = self.patterns
            
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, pattern in enumerate(patterns, 1):
                    f.write(f'[Event "Pattern #{i}"]\n')
                    f.write(f'[Site "Pattern Catalog"]\n')
                    f.write(f'[Date "{datetime.now().strftime("%Y.%m.%d")}"]\n')
                    f.write(f'[Round "{i}"]\n')
                    f.write(f'[White "?"]\n')
                    f.write(f'[Black "?"]\n')
                    f.write(f'[Result "*"]\n')
                    f.write(f'[FEN "{pattern.fen}"]\n')
                    f.write(f'[PatternTypes "{", ".join(pattern.pattern_types)}"]\n')
                    f.write(f'[Description "{pattern.description}"]\n')
                    f.write(f'\n{pattern.move}\n\n')
                    
            logger.info(f"Exported {len(patterns)} patterns to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to export patterns: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the pattern catalog"""
        if not self.patterns:
            return {"total": 0}
        
        # Count by type
        type_counts = {}
        for pattern in self.patterns:
            for pt in pattern.pattern_types:
                type_counts[pt] = type_counts.get(pt, 0) + 1
        
        # Average evaluation change
        eval_changes = [abs(p.evaluation.get("change", 0)) for p in self.patterns]
        avg_eval_change = sum(eval_changes) / len(eval_changes) if eval_changes else 0
        
        # Opening vs endgame
        opening_count = len([p for p in self.patterns if p.metadata.get("fullmove_number", 100) <= 10])
        endgame_count = len([p for p in self.patterns if PatternType.ENDGAME_TECHNIQUE in p.pattern_types])
        
        return {
            "total": len(self.patterns),
            "by_type": type_counts,
            "avg_eval_change": avg_eval_change,
            "opening_patterns": opening_count,
            "endgame_patterns": endgame_count
        }
