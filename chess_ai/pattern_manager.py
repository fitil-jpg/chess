"""
Enhanced pattern management system for chess patterns.
Allows selection of active patterns and custom pattern creation.
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import logging

from chess_ai.pattern_detector import ChessPattern, PatternType

logger = logging.getLogger(__name__)


class PatternManager:
    """Enhanced pattern manager with active pattern selection and custom patterns"""
    
    def __init__(self, patterns_dir: str = "patterns"):
        self.patterns_dir = Path(patterns_dir)
        self.patterns_dir.mkdir(exist_ok=True)
        
        # Pattern storage
        self.all_patterns: List[ChessPattern] = []
        self.active_patterns: Set[str] = set()  # Pattern IDs that are active
        self.custom_patterns: List[ChessPattern] = []
        
        # Pattern configuration
        self.config_file = self.patterns_dir / "pattern_config.json"
        self.pattern_catalog_file = self.patterns_dir / "pattern_catalog.json"
        
        # Load existing data
        self._load_configuration()
        self._load_patterns()
        
    def _load_configuration(self):
        """Load pattern configuration including active patterns"""
        if not self.config_file.exists():
            # Create default configuration
            self._save_configuration()
            return
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            self.active_patterns = set(config.get("active_patterns", []))
            logger.info(f"Loaded configuration with {len(self.active_patterns)} active patterns")
            
        except Exception as e:
            logger.error(f"Failed to load pattern configuration: {e}")
            self.active_patterns = set()
    
    def _save_configuration(self):
        """Save pattern configuration"""
        try:
            config = {
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "active_patterns": list(self.active_patterns),
                "pattern_filters": {
                    "min_eval_change": 50,
                    "max_patterns_per_type": 100,
                    "enable_custom_patterns": True
                }
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Failed to save pattern configuration: {e}")
    
    def _load_patterns(self):
        """Load all patterns from catalog and custom patterns"""
        # Load from catalog
        if self.pattern_catalog_file.exists():
            try:
                with open(self.pattern_catalog_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                self.all_patterns = [ChessPattern.from_dict(p) for p in data.get("patterns", [])]
                logger.info(f"Loaded {len(self.all_patterns)} patterns from catalog")
                
            except Exception as e:
                logger.error(f"Failed to load pattern catalog: {e}")
                self.all_patterns = []
        
        # Load custom patterns
        custom_file = self.patterns_dir / "custom_patterns.json"
        if custom_file.exists():
            try:
                with open(custom_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                self.custom_patterns = [ChessPattern.from_dict(p) for p in data.get("patterns", [])]
                logger.info(f"Loaded {len(self.custom_patterns)} custom patterns")
                
            except Exception as e:
                logger.error(f"Failed to load custom patterns: {e}")
                self.custom_patterns = []
    
    def _save_patterns(self):
        """Save all patterns to their respective files"""
        # Save catalog patterns
        try:
            catalog_data = {
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "count": len(self.all_patterns),
                "patterns": [p.to_dict() for p in self.all_patterns]
            }
            
            with open(self.pattern_catalog_file, 'w', encoding='utf-8') as f:
                json.dump(catalog_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Failed to save pattern catalog: {e}")
        
        # Save custom patterns
        try:
            custom_data = {
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "count": len(self.custom_patterns),
                "patterns": [p.to_dict() for p in self.custom_patterns]
            }
            
            with open(self.patterns_dir / "custom_patterns.json", 'w', encoding='utf-8') as f:
                json.dump(custom_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Failed to save custom patterns: {e}")
    
    def get_pattern_id(self, pattern: ChessPattern) -> str:
        """Generate unique ID for pattern"""
        # Use FEN + move + types as ID
        pattern_key = f"{pattern.fen}_{pattern.move}_{'_'.join(sorted(pattern.pattern_types))}"
        return str(hash(pattern_key))
    
    def add_pattern(self, pattern: ChessPattern, is_custom: bool = False) -> str:
        """Add a new pattern and return its ID"""
        pattern_id = self.get_pattern_id(pattern)
        
        # Add timestamp
        pattern.metadata["added_at"] = datetime.now().isoformat()
        pattern.metadata["pattern_id"] = pattern_id
        pattern.metadata["is_custom"] = is_custom
        
        if is_custom:
            self.custom_patterns.append(pattern)
        else:
            self.all_patterns.append(pattern)
        
        # Auto-activate new patterns
        self.active_patterns.add(pattern_id)
        
        self._save_patterns()
        self._save_configuration()
        
        logger.info(f"Added {'custom' if is_custom else 'catalog'} pattern: {pattern_id}")
        return pattern_id
    
    def remove_pattern(self, pattern_id: str) -> bool:
        """Remove pattern by ID"""
        # Remove from all patterns
        self.all_patterns = [p for p in self.all_patterns if p.metadata.get("pattern_id") != pattern_id]
        
        # Remove from custom patterns
        self.custom_patterns = [p for p in self.custom_patterns if p.metadata.get("pattern_id") != pattern_id]
        
        # Remove from active patterns
        self.active_patterns.discard(pattern_id)
        
        self._save_patterns()
        self._save_configuration()
        
        logger.info(f"Removed pattern: {pattern_id}")
        return True
    
    def set_active_patterns(self, pattern_ids: Set[str]):
        """Set which patterns are active"""
        self.active_patterns = set(pattern_ids)
        self._save_configuration()
        logger.info(f"Set {len(self.active_patterns)} active patterns")
    
    def get_active_patterns(self) -> List[ChessPattern]:
        """Get all currently active patterns"""
        active_patterns = []
        
        # Add from all patterns
        for pattern in self.all_patterns:
            pattern_id = pattern.metadata.get("pattern_id")
            if pattern_id and pattern_id in self.active_patterns:
                active_patterns.append(pattern)
        
        # Add from custom patterns
        for pattern in self.custom_patterns:
            pattern_id = pattern.metadata.get("pattern_id")
            if pattern_id and pattern_id in self.active_patterns:
                active_patterns.append(pattern)
        
        return active_patterns
    
    def get_patterns_by_type(self, pattern_types: List[str] = None) -> List[ChessPattern]:
        """Get patterns filtered by type"""
        all_patterns = self.all_patterns + self.custom_patterns
        
        if not pattern_types:
            return all_patterns
        
        filtered = []
        for pattern in all_patterns:
            if any(pt in pattern.pattern_types for pt in pattern_types):
                filtered.append(pattern)
        
        return filtered
    
    def create_custom_pattern(
        self,
        fen: str,
        move: str,
        pattern_types: List[str],
        description: str,
        influencing_pieces: List[Dict[str, Any]] = None,
        evaluation: Dict[str, Any] = None
    ) -> str:
        """Create a custom pattern"""
        if evaluation is None:
            evaluation = {"before": {"total": 0}, "after": {"total": 0}, "change": 0}
        
        if influencing_pieces is None:
            influencing_pieces = []
        
        pattern = ChessPattern(
            fen=fen,
            move=move,
            pattern_types=pattern_types,
            description=description,
            influencing_pieces=influencing_pieces,
            evaluation=evaluation,
            metadata={"is_custom": True}
        )
        
        return self.add_pattern(pattern, is_custom=True)
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get comprehensive pattern statistics"""
        all_patterns = self.all_patterns + self.custom_patterns
        active_patterns = self.get_active_patterns()
        
        # Count by type
        type_counts = {}
        active_type_counts = {}
        
        for pattern in all_patterns:
            for pt in pattern.pattern_types:
                type_counts[pt] = type_counts.get(pt, 0) + 1
        
        for pattern in active_patterns:
            for pt in pattern.pattern_types:
                active_type_counts[pt] = active_type_counts.get(pt, 0) + 1
        
        # Evaluation statistics
        eval_changes = [abs(p.evaluation.get("change", 0)) for p in all_patterns]
        avg_eval_change = sum(eval_changes) / len(eval_changes) if eval_changes else 0
        
        return {
            "total_patterns": len(all_patterns),
            "active_patterns": len(active_patterns),
            "custom_patterns": len(self.custom_patterns),
            "catalog_patterns": len(self.all_patterns),
            "type_counts": type_counts,
            "active_type_counts": active_type_counts,
            "avg_eval_change": avg_eval_change,
            "active_percentage": (len(active_patterns) / len(all_patterns) * 100) if all_patterns else 0
        }
    
    def export_patterns(self, output_file: str, pattern_ids: List[str] = None) -> bool:
        """Export selected patterns to file"""
        try:
            if pattern_ids:
                # Export specific patterns
                patterns_to_export = []
                for pattern in self.all_patterns + self.custom_patterns:
                    pattern_id = pattern.metadata.get("pattern_id")
                    if pattern_id in pattern_ids:
                        patterns_to_export.append(pattern)
            else:
                # Export all active patterns
                patterns_to_export = self.get_active_patterns()
            
            export_data = {
                "version": "1.0",
                "exported": datetime.now().isoformat(),
                "count": len(patterns_to_export),
                "patterns": [p.to_dict() for p in patterns_to_export]
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(patterns_to_export)} patterns to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export patterns: {e}")
            return False
    
    def import_patterns(self, import_file: str) -> int:
        """Import patterns from file"""
        try:
            with open(import_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            imported_count = 0
            for pattern_data in data.get("patterns", []):
                pattern = ChessPattern.from_dict(pattern_data)
                pattern.metadata["imported_at"] = datetime.now().isoformat()
                self.all_patterns.append(pattern)
                imported_count += 1
            
            self._save_patterns()
            logger.info(f"Imported {imported_count} patterns from {import_file}")
            return imported_count
            
        except Exception as e:
            logger.error(f"Failed to import patterns: {e}")
            return 0