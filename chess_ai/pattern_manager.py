"""
Pattern Manager - управление шахматными паттернами
==================================================

Система управления паттернами:
- Выбор паттернов для использования
- Добавление новых паттернов
- Удаление паттернов
- Фильтрация и поиск
"""

from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass

from chess_ai.enhanced_pattern_detector import EnhancedPattern, EnhancedPatternDetector

logger = logging.getLogger(__name__)


@dataclass
class PatternConfig:
    """Configuration for pattern usage."""
    enabled_types: Set[str]  # Which pattern types to use
    min_confidence: float = 0.5  # Minimum confidence threshold
    prefer_exchanges: bool = True  # Prefer patterns with exchange sequences
    max_patterns_per_position: int = 5  # Maximum patterns to apply per position
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled_types": list(self.enabled_types),
            "min_confidence": self.min_confidence,
            "prefer_exchanges": self.prefer_exchanges,
            "max_patterns_per_position": self.max_patterns_per_position
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PatternConfig:
        return cls(
            enabled_types=set(data.get("enabled_types", [])),
            min_confidence=data.get("min_confidence", 0.5),
            prefer_exchanges=data.get("prefer_exchanges", True),
            max_patterns_per_position=data.get("max_patterns_per_position", 5)
        )


class PatternManager:
    """
    Управляет коллекцией паттернов и их применением.
    
    Основные функции:
    1. Загрузка/сохранение паттернов
    2. Фильтрация по типу, фазе игры, уверенности
    3. Добавление/удаление паттернов
    4. Экспорт/импорт конфигураций
    """
    
    def __init__(self, patterns_dir: str = "patterns/detected"):
        self.detector = EnhancedPatternDetector(patterns_dir)
        self.config_path = Path(patterns_dir) / "config.json"
        self.config = self._load_config()
        
        # Available pattern types
        self.available_types = {
            "fork", "pin", "skewer", "discovered_attack",
            "capture", "check", "exchange", "centralization",
            "tactical", "positional", "opening", "endgame"
        }
    
    def _load_config(self) -> PatternConfig:
        """Load pattern configuration."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return PatternConfig.from_dict(data)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")
        
        # Default config - enable common tactical patterns
        return PatternConfig(
            enabled_types={"fork", "pin", "exchange", "capture", "check"},
            min_confidence=0.5,
            prefer_exchanges=True,
            max_patterns_per_position=3
        )
    
    def save_config(self):
        """Save pattern configuration."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_dict(), f, indent=2)
            logger.info(f"Saved pattern config to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def enable_pattern_type(self, pattern_type: str):
        """Enable a pattern type."""
        if pattern_type in self.available_types:
            self.config.enabled_types.add(pattern_type)
            self.save_config()
            logger.info(f"Enabled pattern type: {pattern_type}")
    
    def disable_pattern_type(self, pattern_type: str):
        """Disable a pattern type."""
        if pattern_type in self.config.enabled_types:
            self.config.enabled_types.discard(pattern_type)
            self.save_config()
            logger.info(f"Disabled pattern type: {pattern_type}")
    
    def set_enabled_types(self, pattern_types: List[str]):
        """Set which pattern types are enabled."""
        self.config.enabled_types = set(pt for pt in pattern_types if pt in self.available_types)
        self.save_config()
        logger.info(f"Enabled pattern types: {self.config.enabled_types}")
    
    def get_enabled_types(self) -> List[str]:
        """Get list of enabled pattern types."""
        return list(self.config.enabled_types)
    
    def add_pattern(self, pattern: EnhancedPattern) -> bool:
        """Add a new pattern to the collection."""
        try:
            self.detector.save_pattern(pattern)
            return True
        except Exception as e:
            logger.error(f"Failed to add pattern: {e}")
            return False
    
    def remove_pattern(self, pattern_id: str) -> bool:
        """Remove a pattern from the collection."""
        return self.detector.delete_pattern(pattern_id)
    
    def get_pattern(self, pattern_id: str) -> Optional[EnhancedPattern]:
        """Get a specific pattern by ID."""
        return self.detector.load_pattern(pattern_id)
    
    def list_patterns(
        self,
        pattern_type: Optional[str] = None,
        game_phase: Optional[str] = None,
        enabled_only: bool = True
    ) -> List[str]:
        """
        List pattern IDs with optional filtering.
        
        Args:
            pattern_type: Filter by pattern type
            game_phase: Filter by game phase (opening, middlegame, endgame)
            enabled_only: Only list patterns of enabled types
            
        Returns:
            List of pattern IDs
        """
        all_patterns = self.detector.list_patterns(pattern_type)
        
        if not (game_phase or enabled_only):
            return all_patterns
        
        filtered = []
        for pattern_id in all_patterns:
            pattern = self.get_pattern(pattern_id)
            if not pattern:
                continue
            
            # Check if type is enabled
            if enabled_only and pattern.pattern_type not in self.config.enabled_types:
                continue
            
            # Check game phase
            if game_phase:
                pattern_phase = pattern.evaluation.get("game_phase", "unknown")
                if pattern_phase != game_phase:
                    continue
            
            filtered.append(pattern_id)
        
        return filtered
    
    def get_patterns_for_position(
        self,
        fen: str,
        max_results: int = None
    ) -> List[EnhancedPattern]:
        """
        Get patterns matching or similar to a FEN position.
        
        Args:
            fen: Board position in FEN notation
            max_results: Maximum number of patterns to return
            
        Returns:
            List of matching patterns
        """
        matching = []
        all_pattern_ids = self.list_patterns(enabled_only=True)
        
        for pattern_id in all_pattern_ids:
            pattern = self.get_pattern(pattern_id)
            if pattern and pattern.fen == fen:
                matching.append(pattern)
        
        # Sort by confidence/quality if needed
        if max_results:
            return matching[:max_results]
        
        return matching
    
    def search_patterns(
        self,
        pattern_types: List[str] = None,
        has_exchange: bool = None,
        min_participants: int = None,
        max_participants: int = None
    ) -> List[str]:
        """
        Search for patterns matching criteria.
        
        Args:
            pattern_types: List of pattern types to include
            has_exchange: Filter by presence of exchange sequence
            min_participants: Minimum number of participating pieces
            max_participants: Maximum number of participating pieces
            
        Returns:
            List of matching pattern IDs
        """
        results = []
        
        for pattern_id in self.detector.list_patterns():
            pattern = self.get_pattern(pattern_id)
            if not pattern:
                continue
            
            # Check pattern type
            if pattern_types and pattern.pattern_type not in pattern_types:
                continue
            
            # Check exchange
            if has_exchange is not None:
                has_ex = pattern.exchange_sequence is not None
                if has_ex != has_exchange:
                    continue
            
            # Check participants
            num_participants = len(pattern.participating_pieces)
            if min_participants and num_participants < min_participants:
                continue
            if max_participants and num_participants > max_participants:
                continue
            
            results.append(pattern_id)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the pattern collection."""
        stats = self.detector.get_pattern_statistics()
        
        # Add config info
        stats["enabled_types"] = list(self.config.enabled_types)
        stats["config"] = self.config.to_dict()
        
        return stats
    
    def export_patterns(
        self,
        output_path: str,
        pattern_ids: List[str] = None
    ):
        """
        Export patterns to a single JSON file.
        
        Args:
            output_path: Path to output file
            pattern_ids: Specific patterns to export (None = all)
        """
        if pattern_ids is None:
            pattern_ids = self.detector.list_patterns()
        
        patterns_data = []
        for pattern_id in pattern_ids:
            pattern = self.get_pattern(pattern_id)
            if pattern:
                patterns_data.append(pattern.to_dict())
        
        export_data = {
            "version": "1.0",
            "pattern_count": len(patterns_data),
            "config": self.config.to_dict(),
            "patterns": patterns_data
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(patterns_data)} patterns to {output_path}")
    
    def import_patterns(self, input_path: str) -> int:
        """
        Import patterns from a JSON file.
        
        Args:
            input_path: Path to import file
            
        Returns:
            Number of patterns imported
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        patterns_data = data.get("patterns", [])
        imported_count = 0
        
        for pattern_data in patterns_data:
            try:
                pattern = EnhancedPattern.from_dict(pattern_data)
                if self.add_pattern(pattern):
                    imported_count += 1
            except Exception as e:
                logger.warning(f"Failed to import pattern: {e}")
        
        logger.info(f"Imported {imported_count} patterns from {input_path}")
        return imported_count
    
    def clear_patterns(self, pattern_type: Optional[str] = None):
        """
        Clear patterns from collection.
        
        Args:
            pattern_type: Clear only this type (None = clear all)
        """
        if pattern_type:
            pattern_ids = self.detector.list_patterns(pattern_type)
        else:
            pattern_ids = self.detector.list_patterns()
        
        for pattern_id in pattern_ids:
            self.remove_pattern(pattern_id)
        
        logger.info(f"Cleared {len(pattern_ids)} patterns" + 
                   (f" of type {pattern_type}" if pattern_type else ""))
    
    def create_pattern_from_game(
        self,
        fen: str,
        move_uci: str,
        pattern_type: str,
        description: str = "",
        participating_pieces: List[Dict[str, Any]] = None
    ) -> Optional[EnhancedPattern]:
        """
        Manually create a pattern from game data.
        
        Args:
            fen: Position before the move
            move_uci: Move in UCI format
            pattern_type: Type of pattern
            description: Optional description
            participating_pieces: Optional list of participating pieces
            
        Returns:
            Created pattern or None
        """
        import chess
        from datetime import datetime
        from chess_ai.enhanced_pattern_detector import PieceParticipation
        
        try:
            board = chess.Board(fen)
            move = chess.Move.from_uci(move_uci)
            
            if not board.is_legal(move):
                logger.error(f"Illegal move: {move_uci} for position {fen}")
                return None
            
            # Convert participating pieces if provided
            participants = []
            if participating_pieces:
                for pp_data in participating_pieces:
                    participants.append(PieceParticipation(**pp_data))
            
            # Generate pattern ID
            pattern_id = f"{pattern_type}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # Create pattern
            pattern = EnhancedPattern(
                pattern_id=pattern_id,
                fen=fen,
                triggering_move=move_uci,
                pattern_type=pattern_type,
                participating_pieces=participants,
                exchange_sequence=None,
                evaluation={
                    "material_balance": 0,
                    "piece_count": len(board.piece_map()),
                    "game_phase": "unknown",
                    "is_check": False,
                    "is_capture": board.is_capture(move)
                },
                metadata={
                    "created_at": datetime.now().isoformat(),
                    "description": description,
                    "manual_creation": True
                }
            )
            
            if self.add_pattern(pattern):
                return pattern
            
        except Exception as e:
            logger.error(f"Failed to create pattern: {e}")
        
        return None
