"""
Pattern Responder for Chess Move Evaluation

This module implements pattern matching and response generation for chess positions,
integrating with WFC and BSP engines for comprehensive pattern analysis.
"""

import chess
import json
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class PatternTemplate:
    """Template for a chess pattern."""
    situation: str  # FEN board position
    action: str     # UCI move or action
    pattern_type: str  # "opening", "tactical", "endgame", "positional"
    confidence: float = 1.0
    frequency: float = 1.0
    description: str = ""


class PatternResponder:
    """
    Loads pattern templates and finds matching actions.
    
    A pattern is a mapping with two keys:
    ``situation`` – the piece placement portion of a FEN string,
    and ``action`` – an arbitrary response (usually a move in UCI format).
    """
    
    def __init__(self, patterns_file: Optional[str] = None):
        self.patterns: List[PatternTemplate] = []
        self.patterns_file = patterns_file or "patterns.json"
        self._load_patterns()
        
    def _load_patterns(self):
        """Load patterns from file or create default patterns."""
        try:
            if Path(self.patterns_file).exists():
                with open(self.patterns_file, 'r') as f:
                    data = json.load(f)
                    for pattern_data in data.get('patterns', []):
                        pattern = PatternTemplate(**pattern_data)
                        self.patterns.append(pattern)
                logger.info(f"Loaded {len(self.patterns)} patterns from {self.patterns_file}")
            else:
                self._create_default_patterns()
                self._save_patterns()
        except Exception as e:
            logger.warning(f"Failed to load patterns: {e}")
            self._create_default_patterns()
    
    def _create_default_patterns(self):
        """Create default pattern templates."""
        # COW Opening patterns
        cow_patterns = [
            PatternTemplate(
                situation="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                action="e2e4",
                pattern_type="opening",
                confidence=0.9,
                frequency=0.8,
                description="COW Opening: King's Pawn"
            ),
            PatternTemplate(
                situation="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
                action="e7e6",
                pattern_type="opening",
                confidence=0.9,
                frequency=0.7,
                description="COW Opening: Black King's Pawn"
            ),
            PatternTemplate(
                situation="rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2",
                action="d2d3",
                pattern_type="opening",
                confidence=0.8,
                frequency=0.6,
                description="COW Opening: Queen's Pawn"
            ),
            PatternTemplate(
                situation="rnbqkbnr/pppp1ppp/8/4p3/4P3/3P4/PPP2PPP/RNBQKBNR b KQkq - 0 2",
                action="d7d6",
                pattern_type="opening",
                confidence=0.8,
                frequency=0.6,
                description="COW Opening: Black Queen's Pawn"
            ),
            PatternTemplate(
                situation="rnbqkbnr/pppp1ppp/8/4p3/4P3/3P4/PPP2PPP/RNBQKBNR b KQkq - 0 2",
                action="g8g6",
                pattern_type="opening",
                confidence=0.7,
                frequency=0.5,
                description="COW Opening: Knight Development"
            ),
            PatternTemplate(
                situation="rnbqkbnr/pppp1ppp/8/4p3/4P3/3P4/PPP2PPP/RNBQKBNR b KQkq - 0 2",
                action="b8b6",
                pattern_type="opening",
                confidence=0.7,
                frequency=0.5,
                description="COW Opening: Knight Development"
            )
        ]
        
        # Tactical patterns
        tactical_patterns = [
            PatternTemplate(
                situation="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                action="fork_check",
                pattern_type="tactical",
                confidence=0.6,
                frequency=0.3,
                description="Fork pattern detection"
            ),
            PatternTemplate(
                situation="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                action="pin_check",
                pattern_type="tactical",
                confidence=0.6,
                frequency=0.3,
                description="Pin pattern detection"
            ),
            PatternTemplate(
                situation="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                action="skewer_check",
                pattern_type="tactical",
                confidence=0.6,
                frequency=0.2,
                description="Skewer pattern detection"
            )
        ]
        
        # Endgame patterns
        endgame_patterns = [
            PatternTemplate(
                situation="8/8/8/8/8/8/8/K7 w - - 0 1",
                action="king_centralization",
                pattern_type="endgame",
                confidence=0.8,
                frequency=0.9,
                description="King centralization in endgame"
            ),
            PatternTemplate(
                situation="8/8/8/8/8/8/8/K7 w - - 0 1",
                action="pawn_promotion",
                pattern_type="endgame",
                confidence=0.9,
                frequency=0.7,
                description="Pawn promotion pattern"
            )
        ]
        
        self.patterns.extend(cow_patterns)
        self.patterns.extend(tactical_patterns)
        self.patterns.extend(endgame_patterns)
        
        logger.info(f"Created {len(self.patterns)} default patterns")
    
    def _save_patterns(self):
        """Save patterns to file."""
        try:
            data = {
                "patterns": [
                    {
                        "situation": p.situation,
                        "action": p.action,
                        "pattern_type": p.pattern_type,
                        "confidence": p.confidence,
                        "frequency": p.frequency,
                        "description": p.description
                    }
                    for p in self.patterns
                ]
            }
            
            with open(self.patterns_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Saved {len(self.patterns)} patterns to {self.patterns_file}")
            
        except Exception as e:
            logger.error(f"Failed to save patterns: {e}")
    
    def match(self, board: chess.Board) -> Optional[str]:
        """
        Return the action for the current board state, if any.
        
        Args:
            board: Current chess board position
            
        Returns:
            Action string if pattern matches, None otherwise
        """
        layout = board.board_fen()
        
        # Find best matching pattern
        best_match = None
        best_confidence = 0.0
        
        for pattern in self.patterns:
            if self._pattern_matches(pattern, layout):
                if pattern.confidence > best_confidence:
                    best_match = pattern
                    best_confidence = pattern.confidence
        
        return best_match.action if best_match else None
    
    def _pattern_matches(self, pattern: PatternTemplate, layout: str) -> bool:
        """Check if a pattern matches the current board layout."""
        # Simple exact match for now - can be enhanced with fuzzy matching
        return pattern.situation == layout
    
    def add_pattern(self, pattern: PatternTemplate):
        """Add a new pattern to the collection."""
        self.patterns.append(pattern)
        self._save_patterns()
        logger.info(f"Added pattern: {pattern.description}")
    
    def get_patterns_by_type(self, pattern_type: str) -> List[PatternTemplate]:
        """Get all patterns of a specific type."""
        return [p for p in self.patterns if p.pattern_type == pattern_type]
    
    def get_opening_patterns(self) -> List[PatternTemplate]:
        """Get all opening patterns."""
        return self.get_patterns_by_type("opening")
    
    def get_tactical_patterns(self) -> List[PatternTemplate]:
        """Get all tactical patterns."""
        return self.get_patterns_by_type("tactical")
    
    def get_endgame_patterns(self) -> List[PatternTemplate]:
        """Get all endgame patterns."""
        return self.get_patterns_by_type("endgame")
    
    def analyze_position(self, board: chess.Board) -> Dict[str, Any]:
        """Analyze current position and return pattern analysis."""
        layout = board.board_fen()
        matches = []
        
        for pattern in self.patterns:
            if self._pattern_matches(pattern, layout):
                matches.append({
                    "pattern_type": pattern.pattern_type,
                    "action": pattern.action,
                    "confidence": pattern.confidence,
                    "description": pattern.description
                })
        
        return {
            "layout": layout,
            "matches": matches,
            "total_patterns": len(self.patterns),
            "matching_patterns": len(matches)
        }
    
    def get_pattern_statistics(self) -> Dict[str, int]:
        """Get statistics about loaded patterns."""
        stats = {}
        for pattern in self.patterns:
            pattern_type = pattern.pattern_type
            stats[pattern_type] = stats.get(pattern_type, 0) + 1
        return stats


# Factory function
def create_pattern_responder(patterns_file: Optional[str] = None) -> PatternResponder:
    """Create a pattern responder with default or custom patterns."""
    return PatternResponder(patterns_file)


# Example usage
if __name__ == "__main__":
    # Create pattern responder
    responder = create_pattern_responder()
    
    # Create a test board
    board = chess.Board()
    
    # Test pattern matching
    action = responder.match(board)
    print(f"Pattern match for starting position: {action}")
    
    # Analyze position
    analysis = responder.analyze_position(board)
    print(f"Position analysis: {analysis}")
    
    # Get statistics
    stats = responder.get_pattern_statistics()
    print(f"Pattern statistics: {stats}")