"""
Pattern Responder for Chess Move Evaluation

This module implements pattern matching and response generation for chess positions,
integrating with WFC and BSP engines for comprehensive pattern analysis.
"""

import chess
import json
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class PatternTemplate:
    """Template for a chess pattern.

    Fields:
    - situation: piece placement FEN (board_fen) or full FEN string
    - action: UCI move or symbolic action (e.g. "fork_check")
    - pattern_type: one of opening|tactical|endgame|positional
    - name: optional human-friendly name (used for filtering)
    - enabled: optional flag to enable/disable this pattern (default True)
    - tags: optional list of string tags for grouping
    - confidence/frequency/description: metadata
    """
    situation: str  # FEN board position
    action: str     # UCI move or action
    pattern_type: str  # "opening", "tactical", "endgame", "positional"
    confidence: float = 1.0
    frequency: float = 1.0
    description: str = ""
    name: str = ""
    enabled: bool = True
    tags: List[str] = None  # type: ignore


class PatternResponder:
    """
    Loads pattern templates and finds matching actions.
    
    A pattern is a mapping with two keys:
    ``situation`` – the piece placement portion of a FEN string,
    and ``action`` – an arbitrary response (usually a move in UCI format).
    """
    
    def __init__(self, patterns_file: Optional[str] = None):
        self.patterns: List[PatternTemplate] = []
        # Allow passing either a file or a directory aggregator via configs/patterns.json
        self.patterns_file = patterns_file or "patterns.json"
        self._load_patterns()
        
    def _load_patterns(self):
        """Load patterns from file(s) or create defaults.

        Supports two modes:
        1) Simple file with {"patterns": [...]} (backward compatible)
        2) Aggregator with optional fields:
           - includes: ["patterns/openings.json", ...]
           - enabled_types: ["opening","tactical",...]
           - enabled_names: ["My Pattern", ...]
           - disabled_names: ["Deprecated Pattern", ...]
        Each included file can be either {"patterns": [...]} or a raw list.
        Patterns with enabled=false are skipped.
        """
        try:
            p = Path(self.patterns_file)
            if p.exists() and p.is_file():
                with p.open('r', encoding='utf-8') as f:
                    data = json.load(f)

                includes = []
                enabled_types = None
                enabled_names = None
                disabled_names = None

                if isinstance(data, dict):
                    # Local inline patterns first
                    raw_patterns = data.get('patterns', [])
                    self._ingest_patterns(raw_patterns)
                    # Optional aggregator controls
                    includes = data.get('includes', []) or []
                    enabled_types = data.get('enabled_types')
                    enabled_names = data.get('enabled_names')
                    disabled_names = data.get('disabled_names')
                else:
                    # Direct list
                    self._ingest_patterns(data)

                # Expand includes
                for inc in includes:
                    inc_path = (p.parent / inc).resolve()
                    if inc_path.is_dir():
                        for child in sorted(inc_path.glob('*.json')):
                            self._ingest_from_file(child)
                    elif inc_path.is_file():
                        self._ingest_from_file(inc_path)

                # Apply filters
                if enabled_types:
                    types_set = set(enabled_types)
                    self.patterns = [pt for pt in self.patterns if pt.pattern_type in types_set]
                if enabled_names:
                    name_set = set(enabled_names)
                    self.patterns = [pt for pt in self.patterns if (pt.name or pt.description) in name_set]
                if disabled_names:
                    dis_set = set(disabled_names)
                    self.patterns = [pt for pt in self.patterns if (pt.name or pt.description) not in dis_set]

                logger.info(f"Loaded {len(self.patterns)} patterns from {self.patterns_file}")
            else:
                self._create_default_patterns()
                self._save_patterns()
        except Exception as e:
            logger.warning(f"Failed to load patterns: {e}")
            self._create_default_patterns()

    def _ingest_from_file(self, inc_path: Path) -> None:
        try:
            with inc_path.open('r', encoding='utf-8') as fh:
                data = json.load(fh)
            raw = data.get('patterns', data)
            self._ingest_patterns(raw)
            logger.info(f"Included {inc_path}")
        except Exception as exc:
            logger.warning(f"Failed to include patterns from {inc_path}: {exc}")

    def _ingest_patterns(self, raw_patterns: Any) -> None:
        for pattern_data in (raw_patterns or []):
            try:
                # Skip disabled
                if isinstance(pattern_data, dict) and pattern_data.get('enabled') is False:
                    continue
                # Provide defaults for optional fields
                if isinstance(pattern_data, dict):
                    pattern_data.setdefault('name', pattern_data.get('description', ""))
                    pattern_data.setdefault('enabled', True)
                    pattern_data.setdefault('tags', [])
                pattern = PatternTemplate(**pattern_data)
                self.patterns.append(pattern)
            except Exception as exc:
                logger.warning(f"Skipping invalid pattern entry {pattern_data}: {exc}")
    
    def _create_default_patterns(self):
        """Create default pattern templates with 90% COW opening target."""
        # Enhanced COW Opening patterns (90% minimum usage target)
        cow_patterns = [
            # Primary COW opening sequence
            PatternTemplate(
                situation="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                action="e2e4",
                pattern_type="opening",
                confidence=0.95,
                frequency=0.9,
                description="COW Opening: King's Pawn (Primary)"
            ),
            PatternTemplate(
                situation="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
                action="e7e6",
                pattern_type="opening",
                confidence=0.9,
                frequency=0.85,
                description="COW Opening: Black Response - French Defense"
            ),
            PatternTemplate(
                situation="rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2",
                action="d2d3",
                pattern_type="opening",
                confidence=0.85,
                frequency=0.8,
                description="COW Opening: Queen's Pawn Support"
            ),
            PatternTemplate(
                situation="rnbqkbnr/pppp1ppp/8/4p3/4P3/3P4/PPP2PPP/RNBQKBNR b KQkq - 0 2",
                action="d7d6",
                pattern_type="opening",
                confidence=0.85,
                frequency=0.75,
                description="COW Opening: Black Queen's Pawn Support"
            ),
            
            # COW development patterns
            PatternTemplate(
                situation="rnbqkbnr/pppp1ppp/8/4p3/4P3/3P4/PPP2PPP/RNBQKBNR b KQkq - 0 2",
                action="g8f6",
                pattern_type="opening",
                confidence=0.8,
                frequency=0.7,
                description="COW Opening: Knight to f6 (Primary Development)"
            ),
            PatternTemplate(
                situation="rnbqkb1r/pppp1ppp/5n2/4p3/4P3/3P4/PPP2PPP/RNBQKBNR w KQkq - 1 3",
                action="f1d3",
                pattern_type="opening",
                confidence=0.8,
                frequency=0.7,
                description="COW Opening: Bishop to d3 (Development)"
            ),
            PatternTemplate(
                situation="rnbqkb1r/pppp1ppp/5n2/4p3/4P3/3P2P1/PPP2PP1/RNBQK2R b KQkq - 0 3",
                action="f8e7",
                pattern_type="opening",
                confidence=0.75,
                frequency=0.65,
                description="COW Opening: Bishop to e7 (Black Development)"
            ),
            
            # COW middlegame transition patterns
            PatternTemplate(
                situation="rnbqk2r/pppp1ppp/5n2/2b1p3/4P3/3P2P1/PPP2PP1/RNBQK2R w KQkq - 1 4",
                action="c2c4",
                pattern_type="opening",
                confidence=0.75,
                frequency=0.6,
                description="COW Opening: Queenside Expansion"
            ),
            PatternTemplate(
                situation="rnbqk2r/pppp1ppp/5n2/2b1p3/2P1P3/3P2P1/PP3PP1/RNBQK2R b KQkq c3 0 4",
                action="c7c5",
                pattern_type="opening",
                confidence=0.7,
                frequency=0.6,
                description="COW Opening: Counter-Expansion"
            ),
            
            # Alternative COW variations
            PatternTemplate(
                situation="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                action="d2d4",
                pattern_type="opening",
                confidence=0.6,
                frequency=0.4,
                description="COW Alternative: Queen's Pawn Opening"
            ),
            PatternTemplate(
                situation="rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1",
                action="d7d5",
                pattern_type="opening",
                confidence=0.6,
                frequency=0.4,
                description="COW Alternative: Queen's Gambit Response"
            )
        ]
        
        # Enhanced tactical patterns for blue gradient visualization
        tactical_patterns = [
            # Fork patterns
            PatternTemplate(
                situation="rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 3",
                action="knight_fork",
                pattern_type="tactical",
                confidence=0.85,
                frequency=0.7,
                description="Knight fork: King and Rook"
            ),
            PatternTemplate(
                situation="r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 1 4",
                action="knight_fork_king_queen",
                pattern_type="tactical",
                confidence=0.9,
                frequency=0.8,
                description="Knight fork: King and Queen"
            ),
            PatternTemplate(
                situation="rnbqkb1r/pppp1ppp/5n2/4p3/4P3/8/PPPP1PPP/RNBQK2R w KQkq - 1 4",
                action="bishop_fork",
                pattern_type="tactical",
                confidence=0.75,
                frequency=0.6,
                description="Bishop fork: Minor pieces"
            ),
            
            # Pin patterns
            PatternTemplate(
                situation="rnbqk2r/pppp1ppp/5n2/4p3/3P4/5N2/PPP1PPPP/RNBQKB1R w KQkq - 0 5",
                action="absolute_pin",
                pattern_type="tactical",
                confidence=0.8,
                frequency=0.7,
                description="Absolute pin: Knight to King"
            ),
            PatternTemplate(
                situation="r1bqk2r/pppp1ppp/2n2n2/4p3/3P4/5N2/PPP1PPPP/RNBQKB1R w KQkq - 1 6",
                action="relative_pin",
                pattern_type="tactical",
                confidence=0.7,
                frequency=0.6,
                description="Relative pin: Queen to Knight"
            ),
            
            # Skewer patterns
            PatternTemplate(
                situation="r3k2r/ppp2ppp/2n1b3/4p3/3P4/5N2/PPP1PPPP/RNBQK2R w KQkq - 0 6",
                action="skewer_king_rook",
                pattern_type="tactical",
                confidence=0.85,
                frequency=0.7,
                description="Skewer: King and Rook"
            ),
            PatternTemplate(
                situation="4k3/ppp2ppp/2n1b3/4p3/3P4/5N2/PPP1PPPP/RNBQK2R w KQkq - 0 6",
                action="skewer_king_queen",
                pattern_type="tactical",
                confidence=0.9,
                frequency=0.8,
                description="Skewer: King and Queen"
            ),
            
            # Discovery attack patterns
            PatternTemplate(
                situation="r2qkbnr/ppp1pppp/2n5/3p4/3PP3/5N2/PPP2PPP/RNBQKB1R w KQkq - 0 5",
                action="discovery_check",
                pattern_type="tactical",
                confidence=0.8,
                frequency=0.7,
                description="Discovery check: Knight move"
            ),
            PatternTemplate(
                situation="r2qkbnr/ppp1pppp/2n5/3p4/3PP3/8/PPP2PPP/RNBQKB1R w KQkq - 0 5",
                action="discovery_attack",
                pattern_type="tactical",
                confidence=0.75,
                frequency=0.6,
                description="Discovery attack: Pawn move"
            ),
            
            # Double attack patterns
            PatternTemplate(
                situation="r1bqkbnr/pppp1ppp/2n5/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R w KQkq - 1 5",
                action="double_attack",
                pattern_type="tactical",
                confidence=0.8,
                frequency=0.7,
                description="Double attack: Two pieces"
            ),
            
            # Removal of defender patterns
            PatternTemplate(
                situation="r1bqk2r/pppp1ppp/2n2n2/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R w KQkq - 2 6",
                action="remove_defender",
                pattern_type="tactical",
                confidence=0.75,
                frequency=0.6,
                description="Remove defender: Capture guard"
            ),
            
            # Interference patterns
            PatternTemplate(
                situation="r1bqk2r/pppp1ppp/2n2n2/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R w KQkq - 2 6",
                action="interference",
                pattern_type="tactical",
                confidence=0.7,
                frequency=0.5,
                description="Interference: Block defender"
            ),
            
            # Overloading patterns
            PatternTemplate(
                situation="r1bqk2r/pppp1ppp/2n2n2/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R w KQkq - 2 6",
                action="overloading",
                pattern_type="tactical",
                confidence=0.7,
                frequency=0.5,
                description="Overloading: Multiple threats"
            ),
            
            # Trapping patterns
            PatternTemplate(
                situation="r1bqk2r/pppp1ppp/2n2n2/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R w KQkq - 2 6",
                action="trap_piece",
                pattern_type="tactical",
                confidence=0.75,
                frequency=0.6,
                description="Trap piece: Limit escapes"
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
        if not pattern.enabled:
            return False
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