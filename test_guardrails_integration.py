#!/usr/bin/env python3
"""
Guardrails Statistics Integration Test

Tests the enhanced guardrails statistics functionality
in the enhanced_heatmap_widget.
"""

import chess
import pytest
from unittest.mock import Mock

from ui.enhanced_heatmap_widget import EnhancedHeatmapWidget
from chess_ai.risk_analyzer import RiskAnalyzer, MoveAnalysisStats, MoveAnalysisSummary
from chess_ai.guardrails import Guardrails


def test_guardrails_stats_display():
    """Test that guardrails statistics are displayed correctly."""
    # Create widget
    widget = EnhancedHeatmapWidget()
    
    # Create mock guardrails statistics
    mock_stats = MoveAnalysisSummary(
        total_moves_evaluated=20,
        safe_moves_found=15,
        risky_moves_rejected=5,
        chosen_move="e2e4",
        chosen_by_bot=True,
        analysis_depth=2,
        total_search_nodes=1000,
        rejection_reasons={"Piece under attack": 3, "Material loss expected": 2},
        analysis_time_total_ms=45.5,
        pattern_description="Middlegame with moderate tactical complexity"
    )
    
    # Set guardrails statistics
    widget.set_guardrails_stats(mock_stats)
    
    # Verify statistics are stored
    assert widget.guardrails_stats == mock_stats
    
    # Test statistics display contains expected information
    widget._update_statistics_display()
    stats_text = widget.stats_label.text()
    
    assert "🛡️ Guardrails Analysis" in stats_text
    assert "Total Moves Evaluated: 20" in stats_text
    assert "Safe Moves Found: 15" in stats_text
    assert "Risky Moves Rejected: 5" in stats_text
    assert "Safety Rate: 75.0%" in stats_text
    assert "Analysis Depth: 2 plies" in stats_text
    assert "Selected Move: e2e4 (Bot)" in stats_text
    assert "Piece under attack: 3 moves" in stats_text


def test_move_risk_stats_visualization():
    """Test that individual move risk statistics are visualized correctly."""
    widget = EnhancedHeatmapWidget()
    
    # Create board
    board = chess.Board()
    widget.set_board(board)
    
    # Create mock move risk statistics
    mock_risk_stats = {
        "e2e4": MoveAnalysisStats(
            move_uci="e2e4",
            depth_analyzed=2,
            is_risky=False,
            material_before=1000,
            material_after=1000,
            attackers_count=0,
            defenders_count=1,
            search_nodes=50,
            rejection_reason="",
            analysis_time_ms=2.5
        ),
        "f2f3": MoveAnalysisStats(
            move_uci="f2f3",
            depth_analyzed=2,
            is_risky=True,
            material_before=1000,
            material_after=900,
            attackers_count=2,
            defenders_count=0,
            search_nodes=75,
            rejection_reason="Piece under attack (attackers:2 > defenders:0)",
            analysis_time_ms=3.2
        )
    }
    
    # Set move risk statistics
    widget.set_move_risk_stats(mock_risk_stats)
    
    # Verify statistics are stored
    assert len(widget.move_risk_stats) == 2
    assert "e2e4" in widget.move_risk_stats
    assert "f2f3" in widget.move_risk_stats
    assert widget.move_risk_stats["f2f3"].is_risky == True
    
    # Test visualization update
    widget._update_guardrails_visualization()
    
    # The risky move should be highlighted on the board
    # (f2f3 goes to f3 square)
    f3_square = chess.parse_square("f3")
    row, col = 7 - chess.square_rank(f3_square), chess.square_file(f3_square)
    cell = widget.mini_board_cells[row][col]
    
    # Cell should have guardrails violation styling
    assert "magenta" in cell.styleSheet()


def test_guardrails_toggle():
    """Test that guardrails display can be toggled on/off."""
    widget = EnhancedHeatmapWidget()
    
    # Create mock statistics
    mock_stats = MoveAnalysisSummary(
        total_moves_evaluated=10,
        safe_moves_found=8,
        risky_moves_rejected=2,
        chosen_move=None,
        chosen_by_bot=False,
        analysis_depth=2,
        total_search_nodes=500,
        rejection_reasons={},
        analysis_time_total_ms=25.0,
        pattern_description="Test position"
    )
    
    widget.set_guardrails_stats(mock_stats)
    
    # Initially guardrails should be visible
    widget.show_guardrails.setChecked(True)
    widget._update_statistics_display()
    stats_text = widget.stats_label.text()
    assert "🛡️ Guardrails Analysis" in stats_text
    
    # Toggle off
    widget.show_guardrails.setChecked(False)
    widget._update_statistics_display()
    stats_text = widget.stats_label.text()
    assert "🛡️ Guardrails Analysis" not in stats_text
    
    # Toggle on
    widget.show_guardrails.setChecked(True)
    widget._update_statistics_display()
    stats_text = widget.stats_label.text()
    assert "🛡️ Guardrails Analysis" in stats_text


def test_guardrails_enabled_flag():
    """Test that guardrails can be enabled/disabled."""
    widget = EnhancedHeatmapWidget()
    
    # Create mock risk statistics
    mock_risk_stats = {
        "e2e4": MoveAnalysisStats(
            move_uci="e2e4",
            depth_analyzed=2,
            is_risky=False,
            material_before=1000,
            material_after=1000,
            attackers_count=0,
            defenders_count=1,
            search_nodes=50,
            rejection_reason="",
            analysis_time_ms=2.5
        )
    }
    
    widget.set_move_risk_stats(mock_risk_stats)
    
    # Guardrails should be enabled by default
    assert widget.guardrails_enabled == True
    
    # Disable guardrails
    widget.set_guardrails_enabled(False)
    assert widget.guardrails_enabled == False
    
    # Visualization should be cleared when disabled
    widget._update_guardrails_visualization()
    # No magenta highlighting should be present
    for row in range(8):
        for col in range(8):
            cell = widget.mini_board_cells[row][col]
            assert "magenta" not in cell.styleSheet()


def test_export_includes_guardrails_data():
    """Test that export includes guardrails statistics."""
    widget = EnhancedHeatmapWidget()
    
    # Create mock data
    mock_stats = MoveAnalysisSummary(
        total_moves_evaluated=5,
        safe_moves_found=4,
        risky_moves_rejected=1,
        chosen_move="e2e4",
        chosen_by_bot=False,
        analysis_depth=2,
        total_search_nodes=250,
        rejection_reasons={},
        analysis_time_total_ms=12.5,
        pattern_description="Simple test"
    )
    
    widget.set_guardrails_stats(mock_stats)
    widget.set_move_risk_stats({"e2e4": Mock()})
    
    # Export state
    exported = widget.export_visualization_state()
    
    # Verify guardrails data is included
    assert 'show_guardrails' in exported
    assert 'guardrails_enabled' in exported
    assert 'guardrails_stats' in exported
    assert 'move_risk_stats_count' in exported
    
    assert exported['show_guardrails'] == True
    assert exported['guardrails_enabled'] == True
    assert exported['guardrails_stats'] is not None
    assert exported['move_risk_stats_count'] == 1


if __name__ == "__main__":
    # Run the tests
    test_guardrails_stats_display()
    test_move_risk_stats_visualization()
    test_guardrails_toggle()
    test_guardrails_enabled_flag()
    test_export_includes_guardrails_data()
    
    print("✅ All guardrails statistics tests passed!")
