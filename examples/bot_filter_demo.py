#!/usr/bin/env python3
"""
Bot Filter Example Usage

This script demonstrates how to use the bot filtering system to select
appropriate chess bots based on position characteristics and patterns.
"""

import chess
import logging
from typing import List

# Import the bot filtering system
from chess_ai.bot_filter import (
    BotFilter, FilterCriteria, GamePhase,
    create_bot_filter, create_opening_filter, create_middlegame_filter,
    create_endgame_filter, create_tactical_filter, create_positional_filter
)

# Import pattern responder for pattern-based filtering
from chess_ai.pattern_responder import PatternResponder

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def demo_basic_filtering():
    """Demonstrate basic bot filtering functionality."""
    print("=" * 60)
    print("BASIC BOT FILTERING DEMO")
    print("=" * 60)
    
    # Create bot filter
    bot_filter = create_bot_filter()
    
    # List available bots
    available_bots = bot_filter.list_available_capabilities()
    print(f"Available bots: {available_bots}")
    print()
    
    # Test different positions
    test_positions = [
        ("Opening Position", chess.Board()),
        ("Middlegame Position", chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p3/4P3/2N2N2/PPPP1PPP/R1BQKB1R w KQkq - 2 4")),
        ("Endgame Position", chess.Board("8/8/8/8/8/8/4k3/4K3 w - - 0 1")),
        ("Tactical Position", chess.Board("rnbqkb1r/ppp2ppp/3p1n2/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R w KQkq - 1 5"))
    ]
    
    for name, board in test_positions:
        print(f"--- {name} ---")
        
        # Analyze position
        analysis = bot_filter.position_analyzer.analyze_position(board)
        print(f"Game Phase: {analysis['game_phase'].value}")
        print(f"Piece Count: {analysis['piece_count']}")
        print(f"Material Advantage: {analysis['material_advantage']}")
        print(f"Tactical Opportunities: {analysis['threats']}")
        
        # Get recommended bots
        recommendations = bot_filter.get_recommended_bots(board, available_bots, top_n=3)
        print(f"Top 3 Recommended Bots:")
        for bot_name, score in recommendations:
            capability = bot_filter.get_bot_capability(bot_name)
            print(f"  - {bot_name}: {score:.2f} (Aggressive: {capability.aggressive_tendency:.1f}, Defensive: {capability.defensive_strength:.1f})")
        
        print()


def demo_filter_by_criteria():
    """Demonstrate filtering by specific criteria."""
    print("=" * 60)
    print("FILTER BY CRITERIA DEMO")
    print("=" * 60)
    
    bot_filter = create_bot_filter()
    board = chess.Board()
    available_bots = bot_filter.list_available_capabilities()
    
    # Test different filter types
    filters = [
        ("Opening Filter", create_opening_filter()),
        ("Middlegame Filter", create_middlegame_filter()),
        ("Endgame Filter", create_endgame_filter()),
        ("Tactical Filter", create_tactical_filter()),
        ("Positional Filter", create_positional_filter())
    ]
    
    for filter_name, criteria in filters:
        print(f"--- {filter_name} ---")
        filtered_bots = bot_filter.filter_bots(board, available_bots, criteria)
        print(f"Filtered bots: {filtered_bots}")
        
        # Show why bots were selected
        for bot_name in filtered_bots[:3]:  # Show first 3
            capability = bot_filter.get_bot_capability(bot_name)
            print(f"  {bot_name}:")
            print(f"    Preferred phases: {[p.value for p in capability.preferred_phases]}")
            print(f"    Tactical awareness: {capability.tactical_awareness}")
            print(f"    Aggressive tendency: {capability.aggressive_tendency}")
        print()


def demo_custom_criteria():
    """Demonstrate custom filtering criteria."""
    print("=" * 60)
    print("CUSTOM CRITERIA DEMO")
    print("=" * 60)
    
    bot_filter = create_bot_filter()
    board = chess.Board()
    available_bots = bot_filter.list_available_capabilities()
    
    # Create custom criteria
    custom_filters = [
        ("Very Aggressive Bots", FilterCriteria(
            tactical_awareness=True,
            material_advantage="advantage"
        )),
        ("Defensive Specialists", FilterCriteria(
            defensive_strength=0.8,  # This will be handled in the filter logic
            king_safety_required=True
        )),
        ("Tactical Pattern Matchers", FilterCriteria(
            pattern_types=["tactical"],
            threats_required=True
        )),
        ("Positional Experts", FilterCriteria(
            center_control_required=True,
            pawn_structure_required=True
        ))
    ]
    
    for filter_name, criteria in custom_filters:
        print(f"--- {filter_name} ---")
        filtered_bots = bot_filter.filter_bots(board, available_bots, criteria)
        print(f"Filtered bots: {filtered_bots}")
        print()


def demo_pattern_based_filtering():
    """Demonstrate pattern-based bot filtering."""
    print("=" * 60)
    print("PATTERN-BASED FILTERING DEMO")
    print("=" * 60)
    
    # Create pattern responder
    pattern_responder = PatternResponder()
    
    # Create bot filter with pattern responder
    bot_filter = create_bot_filter(pattern_responder)
    
    # Test positions with specific patterns
    pattern_positions = [
        ("Starting Position", chess.Board(), ["opening"]),
        ("Tactical Position", chess.Board("rnbqkb1r/ppp2ppp/3p1n2/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R w KQkq - 1 5"), ["tactical"]),
        ("Endgame Position", chess.Board("8/8/8/8/8/8/4k3/4K3 w - - 0 1"), ["endgame"])
    ]
    
    for name, board, expected_patterns in pattern_positions:
        print(f"--- {name} ---")
        
        # Analyze patterns
        pattern_analysis = pattern_responder.analyze_position(board)
        print(f"Pattern matches: {len(pattern_analysis['matching_patterns'])}")
        for match in pattern_analysis['matches']:
            print(f"  - {match['pattern_type']}: {match['description']}")
        
        # Filter by pattern types
        criteria = FilterCriteria(pattern_types=expected_patterns)
        available_bots = bot_filter.list_available_capabilities()
        filtered_bots = bot_filter.filter_bots(board, available_bots, criteria)
        
        print(f"Bots matching {expected_patterns} patterns: {filtered_bots}")
        print()


def demo_position_analysis():
    """Demonstrate detailed position analysis."""
    print("=" * 60)
    print("POSITION ANALYSIS DEMO")
    print("=" * 60)
    
    bot_filter = create_bot_filter()
    
    # Analyze different types of positions
    positions = [
        ("Complex Middlegame", "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 6"),
        ("King Safety Issue", "rnbqk2r/pppp1ppp/5n2/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R b KQkq - 2 4"),
        ("Center Control", "rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 4"),
        ("Pawn Structure", "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 1 3")
    ]
    
    for name, fen in positions:
        print(f"--- {name} ---")
        board = chess.Board(fen)
        analysis = bot_filter.position_analyzer.analyze_position(board)
        
        print(f"FEN: {fen}")
        print(f"Game Phase: {analysis['game_phase'].value}")
        print(f"Move Number: {analysis['move_number']}")
        print(f"Material Balance: {analysis['material_balance']:.1f}")
        print(f"Material Advantage: {analysis['material_advantage']}")
        print(f"Center Control: {analysis['center_control']}")
        print(f"King Safety: {analysis['king_safety']}")
        print(f"Pawn Structure: {analysis['pawn_structure']}")
        print(f"Tactical Threats: {analysis['threats']}")
        print(f"Checks Available: {analysis['checks_available']}")
        print(f"Captures Available: {analysis['captures_available']}")
        print()


def demo_bot_capability_management():
    """Demonstrate adding and managing bot capabilities."""
    print("=" * 60)
    print("BOT CAPABILITY MANAGEMENT DEMO")
    print("=" * 60)
    
    bot_filter = create_bot_filter()
    
    # Add custom bot capabilities
    custom_bots = [
        {
            "name": "CustomEndgameExpert",
            "class": "CustomEndgameExpert",
            "phases": [GamePhase.ENDGAME],
            "material": ["advantage", "disadvantage"],
            "tactical": True,
            "aggressive": 0.4,
            "defensive": 0.8,
            "king_safety": True
        },
        {
            "name": "CustomTacticalWizard",
            "class": "CustomTacticalWizard",
            "phases": [GamePhase.MIDDLEGAME],
            "material": ["equal"],
            "tactical": True,
            "aggressive": 0.9,
            "defensive": 0.3,
            "patterns": ["tactical"]
        },
        {
            "name": "CustomPositionalMaster",
            "class": "CustomPositionalMaster",
            "phases": [GamePhase.MIDDLEGAME, GamePhase.ENDGAME],
            "material": ["equal", "advantage"],
            "tactical": False,
            "aggressive": 0.2,
            "defensive": 0.7,
            "center_control": True,
            "pawn_structure": True
        }
    ]
    
    print("Adding custom bot capabilities...")
    for bot_config in custom_bots:
        from chess_ai.bot_filter import BotCapability
        capability = BotCapability(
            bot_name=bot_config["name"],
            bot_class=bot_config["class"],
            preferred_phases=bot_config.get("phases", []),
            material_situations=bot_config.get("material", []),
            tactical_awareness=bot_config.get("tactical", False),
            aggressive_tendency=bot_config.get("aggressive", 0.5),
            defensive_strength=bot_config.get("defensive", 0.5),
            king_safety_awareness=bot_config.get("king_safety", False),
            center_control_focus=bot_config.get("center_control", False),
            pawn_structure_expertise=bot_config.get("pawn_structure", False),
            pattern_types=bot_config.get("patterns", [])
        )
        bot_filter.add_bot_capability(capability)
        print(f"Added: {bot_config['name']}")
    
    print()
    
    # Test filtering with custom bots
    available_bots = bot_filter.list_available_capabilities()
    board = chess.Board()
    
    # Test different scenarios
    scenarios = [
        ("Endgame Scenario", create_endgame_filter()),
        ("Tactical Scenario", create_tactical_filter()),
        ("Positional Scenario", create_positional_filter())
    ]
    
    for scenario_name, criteria in scenarios:
        print(f"--- {scenario_name} ---")
        filtered = bot_filter.filter_bots(board, available_bots, criteria)
        
        # Show custom bots that were selected
        custom_filtered = [bot for bot in filtered if bot.startswith("Custom")]
        print(f"Custom bots selected: {custom_filtered}")
        
        if custom_filtered:
            for bot_name in custom_filtered:
                capability = bot_filter.get_bot_capability(bot_name)
                print(f"  {bot_name}: {[p.value for p in capability.preferred_phases]}")
        print()


def demo_performance_comparison():
    """Demonstrate performance comparison between bots."""
    print("=" * 60)
    print("PERFORMANCE COMPARISON DEMO")
    print("=" * 60)
    
    bot_filter = create_bot_filter()
    
    # Test positions representing different game phases
    test_positions = [
        ("Opening", chess.Board()),
        ("Early Middlegame", chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p3/4P3/2N2N2/PPPP1PPP/R1BQKB1R w KQkq - 2 4")),
        ("Complex Middlegame", chess.Board("r2qkbnr/ppp2ppp/3p1n2/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R w KQkq - 1 6")),
        ("Endgame", chess.Board("8/8/8/8/8/8/4k3/4K3 w - - 0 1"))
    ]
    
    available_bots = ["AggressiveBot", "FortifyBot", "EndgameBot", "DynamicBot", "RandomBot"]
    
    for phase, board in test_positions:
        print(f"--- {phase} Phase ---")
        recommendations = bot_filter.get_recommended_bots(board, available_bots)
        
        print("Bot Rankings:")
        for i, (bot_name, score) in enumerate(recommendations, 1):
            capability = bot_filter.get_bot_capability(bot_name)
            print(f"  {i}. {bot_name}: {score:.3f}")
            print(f"     Aggressive: {capability.aggressive_tendency:.1f}, Defensive: {capability.defensive_strength:.1f}")
            print(f"     Tactical: {capability.tactical_awareness}, Phases: {[p.value for p in capability.preferred_phases]}")
        print()


def main():
    """Main demonstration function."""
    print("CHESS BOT FILTERING SYSTEM DEMO")
    print("=" * 60)
    print()
    
    try:
        # Run all demonstrations
        demo_basic_filtering()
        demo_filter_by_criteria()
        demo_custom_criteria()
        demo_pattern_based_filtering()
        demo_position_analysis()
        demo_bot_capability_management()
        demo_performance_comparison()
        
        print("=" * 60)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print()
        print("Key Features Demonstrated:")
        print("✓ Position-based bot filtering")
        print("✓ Pattern-based bot selection")
        print("✓ Custom filtering criteria")
        print("✓ Detailed position analysis")
        print("✓ Bot capability management")
        print("✓ Performance scoring and ranking")
        print()
        print("The bot filtering system is ready for integration!")
        
    except Exception as e:
        logger.error(f"Demo failed with error: {e}")
        raise


if __name__ == "__main__":
    main()
