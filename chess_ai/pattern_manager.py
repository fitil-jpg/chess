"""
Enhanced pattern management system with individual JSON files and filtering capabilities.
"""

from __future__ import annotations
import json
import os
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import logging
import chess

from chess_ai.pattern_detector import ChessPattern, PatternType

logger = logging.getLogger(__name__)


class PatternManager:
    """Enhanced pattern management with individual JSON files and filtering"""
    
    def __init__(self, patterns_dir: str = "patterns"):
        self.patterns_dir = Path(patterns_dir)
        self.patterns_dir.mkdir(exist_ok=True)
        self.patterns: Dict[str, ChessPattern] = {}
        self.pattern_index: Dict[str, Dict[str, List[str]]] = {
            "by_type": {},
            "by_piece": {},
            "by_phase": {},
            "by_eval_change": {}
        }
        self._load_all_patterns()
    
    def _load_all_patterns(self):
        """Load all patterns from individual JSON files"""
        self.patterns.clear()
        self.pattern_index = {
            "by_type": {},
            "by_piece": {},
            "by_phase": {},
            "by_eval_change": {}
        }
        
        for json_file in self.patterns_dir.glob("*.json"):
            if json_file.name == "catalog.json":
                continue  # Skip old catalog format
                
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                pattern = ChessPattern.from_dict(data)
                pattern_id = data.get("id", str(uuid.uuid4()))
                self.patterns[pattern_id] = pattern
                self._update_index(pattern_id, pattern)
                
            except Exception as e:
                logger.error(f"Failed to load pattern from {json_file}: {e}")
    
    def _update_index(self, pattern_id: str, pattern: ChessPattern):
        """Update search indexes for a pattern"""
        # Debug: check if by_type is a dict
        if not isinstance(self.pattern_index["by_type"], dict):
            logger.error(f"by_type is not a dict: {type(self.pattern_index['by_type'])}")
            return
        
        # Index by pattern types
        for pattern_type in pattern.pattern_types:
            if pattern_type not in self.pattern_index["by_type"]:
                self.pattern_index["by_type"][pattern_type] = []
            self.pattern_index["by_type"][pattern_type].append(pattern_id)
        
        # Index by piece type (from move)
        try:
            board = chess.Board(pattern.fen)
            move = board.parse_san(pattern.move)
            piece = board.piece_at(move.from_square)
            if piece:
                piece_name = self._piece_type_to_name(piece.piece_type)
                if piece_name not in self.pattern_index["by_piece"]:
                    self.pattern_index["by_piece"][piece_name] = []
                self.pattern_index["by_piece"][piece_name].append(pattern_id)
        except:
            pass
        
        # Index by game phase
        move_number = pattern.metadata.get("fullmove_number", 0)
        if move_number <= 10:
            phase = "opening"
        elif move_number <= 30:
            phase = "midgame"
        else:
            phase = "endgame"
        
        if phase not in self.pattern_index["by_phase"]:
            self.pattern_index["by_phase"][phase] = []
        self.pattern_index["by_phase"][phase].append(pattern_id)
        
        # Index by evaluation change
        eval_change = abs(pattern.evaluation.get("change", 0))
        if eval_change > 200:
            eval_range = "high"
        elif eval_change > 100:
            eval_range = "medium"
        else:
            eval_range = "low"
        
        if eval_range not in self.pattern_index["by_eval_change"]:
            self.pattern_index["by_eval_change"][eval_range] = []
        self.pattern_index["by_eval_change"][eval_range].append(pattern_id)
    
    def _piece_type_to_name(self, piece_type: int) -> str:
        """Convert piece type to name"""
        mapping = {
            chess.PAWN: "pawn",
            chess.KNIGHT: "knight",
            chess.BISHOP: "bishop",
            chess.ROOK: "rook",
            chess.QUEEN: "queen",
            chess.KING: "king",
        }
        return mapping.get(piece_type, "unknown")
    
    def add_pattern(self, pattern: ChessPattern) -> str:
        """Add a new pattern and save to individual JSON file"""
        pattern_id = str(uuid.uuid4())
        pattern.metadata["id"] = pattern_id
        pattern.metadata["created_at"] = datetime.now().isoformat()
        
        # Debug: check pattern_index structure
        logger.debug(f"pattern_index type: {type(self.pattern_index)}")
        logger.debug(f"by_type type: {type(self.pattern_index.get('by_type', 'NOT_FOUND'))}")
        
        # Save to individual file
        pattern_file = self.patterns_dir / f"pattern_{pattern_id}.json"
        try:
            with open(pattern_file, 'w', encoding='utf-8') as f:
                json.dump(pattern.to_dict(), f, indent=2, ensure_ascii=False)
            
            self.patterns[pattern_id] = pattern
            self._update_index(pattern_id, pattern)
            logger.info(f"Added pattern {pattern_id}: {pattern.move}")
            return pattern_id
            
        except Exception as e:
            logger.error(f"Failed to save pattern {pattern_id}: {e}")
            raise
    
    def update_pattern(self, pattern_id: str, pattern: ChessPattern) -> bool:
        """Update an existing pattern"""
        if pattern_id not in self.patterns:
            return False
        
        pattern.metadata["id"] = pattern_id
        pattern.metadata["updated_at"] = datetime.now().isoformat()
        
        # Update file
        pattern_file = self.patterns_dir / f"pattern_{pattern_id}.json"
        try:
            with open(pattern_file, 'w', encoding='utf-8') as f:
                json.dump(pattern.to_dict(), f, indent=2, ensure_ascii=False)
            
            self.patterns[pattern_id] = pattern
            self._update_index(pattern_id, pattern)
            logger.info(f"Updated pattern {pattern_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update pattern {pattern_id}: {e}")
            return False
    
    def delete_pattern(self, pattern_id: str) -> bool:
        """Delete a pattern and its file"""
        if pattern_id not in self.patterns:
            return False
        
        # Remove file
        pattern_file = self.patterns_dir / f"pattern_{pattern_id}.json"
        try:
            if pattern_file.exists():
                pattern_file.unlink()
            
            # Remove from memory and indexes
            del self.patterns[pattern_id]
            self._remove_from_indexes(pattern_id)
            logger.info(f"Deleted pattern {pattern_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete pattern {pattern_id}: {e}")
            return False
    
    def _remove_from_indexes(self, pattern_id: str):
        """Remove pattern from all indexes"""
        for index_type in self.pattern_index.values():
            if isinstance(index_type, dict):
                for key, pattern_list in index_type.items():
                    if pattern_id in pattern_list:
                        pattern_list.remove(pattern_id)
    
    def get_pattern(self, pattern_id: str) -> Optional[ChessPattern]:
        """Get a specific pattern by ID"""
        return self.patterns.get(pattern_id)
    
    def search_patterns(
        self,
        pattern_types: List[str] = None,
        piece_types: List[str] = None,
        phases: List[str] = None,
        eval_ranges: List[str] = None,
        min_eval_change: float = None,
        max_eval_change: float = None,
        search_text: str = None
    ) -> List[ChessPattern]:
        """
        Search patterns with multiple filters
        
        Args:
            pattern_types: Filter by pattern types (fork, pin, etc.)
            piece_types: Filter by piece types (pawn, knight, etc.)
            phases: Filter by game phases (opening, midgame, endgame)
            eval_ranges: Filter by evaluation ranges (low, medium, high)
            min_eval_change: Minimum evaluation change
            max_eval_change: Maximum evaluation change
            search_text: Search in description and move text
        """
        candidate_ids = set(self.patterns.keys())
        
        # Filter by pattern types
        if pattern_types:
            type_ids = set()
            for pattern_type in pattern_types:
                type_ids.update(self.pattern_index["by_type"].get(pattern_type, []))
            candidate_ids &= type_ids
        
        # Filter by piece types
        if piece_types:
            piece_ids = set()
            for piece_type in piece_types:
                piece_ids.update(self.pattern_index["by_piece"].get(piece_type, []))
            candidate_ids &= piece_ids
        
        # Filter by phases
        if phases:
            phase_ids = set()
            for phase in phases:
                phase_ids.update(self.pattern_index["by_phase"].get(phase, []))
            candidate_ids &= phase_ids
        
        # Filter by evaluation ranges
        if eval_ranges:
            eval_ids = set()
            for eval_range in eval_ranges:
                eval_ids.update(self.pattern_index["by_eval_change"].get(eval_range, []))
            candidate_ids &= eval_ids
        
        # Get patterns and apply additional filters
        results = []
        for pattern_id in candidate_ids:
            pattern = self.patterns[pattern_id]
            
            # Filter by evaluation change range
            eval_change = abs(pattern.evaluation.get("change", 0))
            if min_eval_change is not None and eval_change < min_eval_change:
                continue
            if max_eval_change is not None and eval_change > max_eval_change:
                continue
            
            # Filter by search text
            if search_text:
                search_lower = search_text.lower()
                if (search_lower not in pattern.description.lower() and 
                    search_lower not in pattern.move.lower()):
                    continue
            
            results.append(pattern)
        
        return results
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about patterns"""
        if not self.patterns:
            return {"total_patterns": 0}
        
        stats = {
            "total_patterns": len(self.patterns),
            "by_type": {},
            "by_piece": {},
            "by_phase": {},
            "by_eval_change": {},
            "recent_patterns": [],
            "top_patterns": []
        }
        
        # Count by type
        for pattern_type, pattern_ids in self.pattern_index["by_type"].items():
            stats["by_type"][pattern_type] = len(pattern_ids)
        
        # Count by piece
        for piece_type, pattern_ids in self.pattern_index["by_piece"].items():
            stats["by_piece"][piece_type] = len(pattern_ids)
        
        # Count by phase
        for phase, pattern_ids in self.pattern_index["by_phase"].items():
            stats["by_phase"][phase] = len(pattern_ids)
        
        # Count by evaluation change
        for eval_range, pattern_ids in self.pattern_index["by_eval_change"].items():
            stats["by_eval_change"][eval_range] = len(pattern_ids)
        
        # Recent patterns (last 10)
        recent_patterns = sorted(
            self.patterns.values(),
            key=lambda p: p.metadata.get("created_at", ""),
            reverse=True
        )[:10]
        stats["recent_patterns"] = [
            {
                "id": p.metadata.get("id", "unknown"),
                "move": p.move,
                "types": p.pattern_types,
                "created_at": p.metadata.get("created_at", "unknown")
            }
            for p in recent_patterns
        ]
        
        # Top patterns by evaluation change
        top_patterns = sorted(
            self.patterns.values(),
            key=lambda p: abs(p.evaluation.get("change", 0)),
            reverse=True
        )[:10]
        stats["top_patterns"] = [
            {
                "id": p.metadata.get("id", "unknown"),
                "move": p.move,
                "types": p.pattern_types,
                "eval_change": p.evaluation.get("change", 0)
            }
            for p in top_patterns
        ]
        
        return stats
    
    def export_patterns(self, output_path: str, pattern_ids: List[str] = None) -> bool:
        """Export selected patterns to a single JSON file"""
        if pattern_ids is None:
            patterns_to_export = list(self.patterns.values())
        else:
            patterns_to_export = [
                self.patterns[pid] for pid in pattern_ids 
                if pid in self.patterns
            ]
        
        try:
            export_data = {
                "version": "2.0",
                "exported_at": datetime.now().isoformat(),
                "count": len(patterns_to_export),
                "patterns": [p.to_dict() for p in patterns_to_export]
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(patterns_to_export)} patterns to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export patterns: {e}")
            return False
    
    def import_patterns(self, import_path: str) -> int:
        """Import patterns from a JSON file"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            imported_count = 0
            patterns = data.get("patterns", [])
            
            for pattern_data in patterns:
                try:
                    pattern = ChessPattern.from_dict(pattern_data)
                    pattern_id = self.add_pattern(pattern)
                    if pattern_id:
                        imported_count += 1
                except Exception as e:
                    logger.warning(f"Failed to import pattern: {e}")
                    continue
            
            logger.info(f"Imported {imported_count} patterns from {import_path}")
            return imported_count
            
        except Exception as e:
            logger.error(f"Failed to import patterns from {import_path}: {e}")
            return 0