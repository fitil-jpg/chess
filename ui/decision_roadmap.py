"""
Decision Roadmap Visualization Module

Provides comprehensive visualization of the move decision-making process
for DynamicBot and other chess AI agents using MoveObject tracking.
"""

from __future__ import annotations

import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import asdict
import chess

from core.move_object import MoveObject, MovePhase, MoveStatus, move_evaluation_manager


class DecisionRoadmap:
    """
    Visualizes the complete decision-making roadmap for chess moves.
    
    This class provides methods to generate, format, and export detailed
    information about how moves are selected, including:
    - Agent contributions and weights
    - Phase-by-phase evaluation
    - Timing breakdown
    - Confidence scoring
    - Tactical analysis
    """
    
    def __init__(self):
        self.current_move: Optional[MoveObject] = None
        self.move_history: List[MoveObject] = []
    
    def update_from_manager(self) -> None:
        """Update roadmap from the global move evaluation manager."""
        if move_evaluation_manager.current_move:
            self.current_move = move_evaluation_manager.current_move
        
        # Update history from manager
        self.move_history = move_evaluation_manager.move_history.copy()
    
    def get_current_roadmap(self) -> Dict[str, Any]:
        """Get the complete roadmap for the current move being evaluated."""
        if not self.current_move:
            return {"status": "no_active_move", "message": "No move currently being evaluated"}
        
        return self._generate_roadmap(self.current_move)
    
    def get_move_roadmap(self, move_index: int = -1) -> Dict[str, Any]:
        """Get roadmap for a specific move from history."""
        if not self.move_history:
            return {"status": "no_history", "message": "No move history available"}
        
        if move_index < 0:
            move_index = len(self.move_history) + move_index
        
        if move_index >= len(self.move_history) or move_index < 0:
            return {"status": "invalid_index", "message": f"Move index {move_index} out of range"}
        
        return self._generate_roadmap(self.move_history[move_index])
    
    def _generate_roadmap(self, move_obj: MoveObject) -> Dict[str, Any]:
        """Generate comprehensive roadmap for a single move object."""
        roadmap = {
            "move_info": {
                "move": move_obj.san_notation or str(move_obj.move),
                "uci": move_obj.move.uci() if move_obj.move else None,
                "move_number": move_obj.move_number,
                "color": "white" if move_obj.color else "black",
                "board_fen": move_obj.board_fen
            },
            "decision_process": {
                "current_phase": move_obj.current_phase.value,
                "status": move_obj.status.value,
                "final_score": move_obj.final_score,
                "confidence": move_obj.confidence,
                "primary_reason": move_obj.primary_reason,
                "total_duration_ms": move_obj.total_duration_ms
            },
            "timing_breakdown": {
                phase.value: duration for phase, duration in move_obj.phase_durations.items()
            },
            "agent_contributions": {},
            "weight_analysis": {},
            "tactical_analysis": {},
            "metadata": move_obj.metadata
        }
        
        # Process agent evaluations
        for bot_name, step in move_obj.bot_evaluations.items():
            roadmap["agent_contributions"][bot_name] = {
                "method": step.method_name,
                "confidence": step.confidence,
                "duration_ms": step.duration_ms,
                "status": step.status.value,
                "reason": step.reason,
                "input_data": step.input_data,
                "output_data": step.output_data,
                "features": step.features
            }
        
        # Process method results
        for method_name, result in move_obj.method_results.items():
            if "weights" not in roadmap["weight_analysis"]:
                roadmap["weight_analysis"]["methods"] = {}
            
            roadmap["weight_analysis"]["methods"][method_name] = {
                "status": result.status.value,
                "value": result.value,
                "confidence": result.confidence,
                "active_in_board": result.active_in_board,
                "processing_time_ms": result.processing_time_ms,
                "reason": result.reason,
                "metadata": result.metadata
            }
        
        # Tactical analysis
        roadmap["tactical_analysis"] = {
            "motifs": move_obj.tactical_motifs,
            "threats": move_obj.tactical_threats,
            "guardrails": {
                "passed": move_obj.guardrails_passed,
                "violations": move_obj.guardrails_violations,
                "warnings": move_obj.guardrails_warnings
            },
            "minimax": {
                "depth": move_obj.minimax_depth,
                "value": move_obj.minimax_value,
                "meets_threshold": move_obj.meets_minimax_threshold,
                "principal_variation": [m.uci() for m in move_obj.minimax_pv]
            }
        }
        
        # Score components
        roadmap["score_breakdown"] = {
            "base_score": move_obj.base_score,
            "pattern_score": move_obj.pattern_score,
            "wfc_score": move_obj.wfc_score,
            "bsp_score": move_obj.bsp_score,
            "heatmap_score": move_obj.heatmap_score,
            "tactical_score": move_obj.tactical_score,
            "positional_score": move_obj.positional_score,
            "minimax_score": move_obj.minimax_score,
            "final_score": move_obj.final_score
        }
        
        # Contributing factors
        roadmap["contributing_factors"] = move_obj.contributing_factors
        
        return roadmap
    
    def get_agent_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for all agents."""
        if not self.move_history:
            return {"status": "no_data", "message": "No move history available"}
        
        agent_stats = {}
        
        for move_obj in self.move_history:
            for bot_name, step in move_obj.bot_evaluations.items():
                if bot_name not in agent_stats:
                    agent_stats[bot_name] = {
                        "total_evaluations": 0,
                        "total_duration_ms": 0.0,
                        "avg_confidence": 0.0,
                        "success_count": 0,
                        "avg_score": 0.0,
                        "moves_contributed": []
                    }
                
                stats = agent_stats[bot_name]
                stats["total_evaluations"] += 1
                stats["total_duration_ms"] += step.duration_ms
                stats["avg_confidence"] = (stats["avg_confidence"] * (stats["total_evaluations"] - 1) + step.confidence) / stats["total_evaluations"]
                
                if step.status == MoveStatus.COMPLETED:
                    stats["success_count"] += 1
                
                if move_obj.final_score > 0:
                    stats["avg_score"] = (stats["avg_score"] * (stats["total_evaluations"] - 1) + move_obj.final_score) / stats["total_evaluations"]
                
                stats["moves_contributed"].append({
                    "move": move_obj.san_notation,
                    "confidence": step.confidence,
                    "score": move_obj.final_score,
                    "duration_ms": step.duration_ms
                })
        
        # Calculate success rates
        for bot_name, stats in agent_stats.items():
            stats["success_rate"] = stats["success_count"] / stats["total_evaluations"]
            stats["avg_duration_ms"] = stats["total_duration_ms"] / stats["total_evaluations"]
        
        return agent_stats
    
    def export_roadmap_json(self, filename: str, include_history: bool = True) -> None:
        """Export roadmap data to JSON file."""
        export_data = {
            "export_timestamp": time.time(),
            "current_move": self.get_current_roadmap(),
            "agent_performance": self.get_agent_performance_summary()
        }
        
        if include_history:
            export_data["move_history"] = [
                self._generate_roadmap(move_obj) for move_obj in self.move_history[-10:]  # Last 10 moves
            ]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def get_console_summary(self, move_index: int = -1) -> str:
        """Get a formatted console summary of the decision roadmap."""
        roadmap = self.get_move_roadmap(move_index)
        
        if "status" in roadmap and roadmap["status"] != "success":
            return f"Error: {roadmap.get('message', 'Unknown error')}"
        
        lines = []
        lines.append("=" * 60)
        lines.append("DECISION ROADMAP SUMMARY")
        lines.append("=" * 60)
        
        # Move info
        move_info = roadmap["move_info"]
        lines.append(f"Move: {move_info['move']} ({move_info['uci']})")
        lines.append(f"Number: {move_info['move_number']} - Color: {move_info['color']}")
        
        # Decision process
        decision = roadmap["decision_process"]
        lines.append(f"Phase: {decision['current_phase']}")
        lines.append(f"Status: {decision['status']}")
        lines.append(f"Final Score: {decision['final_score']:.3f}")
        lines.append(f"Confidence: {decision['confidence']:.3f}")
        lines.append(f"Duration: {decision['total_duration_ms']:.1f}ms")
        lines.append(f"Reason: {decision['primary_reason']}")
        
        # Agent contributions
        if roadmap["agent_contributions"]:
            lines.append("\nAGENT CONTRIBUTIONS:")
            lines.append("-" * 30)
            for agent, contrib in roadmap["agent_contributions"].items():
                lines.append(f"  {agent}:")
                lines.append(f"    Confidence: {contrib['confidence']:.3f}")
                lines.append(f"    Duration: {contrib['duration_ms']:.1f}ms")
                lines.append(f"    Status: {contrib['status']}")
                if contrib.get('output_data', {}).get('move'):
                    lines.append(f"    Suggested: {contrib['output_data']['move']}")
        
        # Score breakdown
        scores = roadmap["score_breakdown"]
        lines.append("\nSCORE BREAKDOWN:")
        lines.append("-" * 20)
        for component, value in scores.items():
            if value != 0:
                lines.append(f"  {component}: {value:.3f}")
        
        # Tactical analysis
        tactical = roadmap["tactical_analysis"]
        if tactical["motifs"]:
            lines.append(f"\nTactical Motifs: {', '.join(tactical['motifs'])}")
        
        if not tactical["guardrails"]["passed"]:
            lines.append(f"Guardrails Issues: {', '.join(tactical['guardrails']['violations'])}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def get_real_time_updates(self) -> Dict[str, Any]:
        """Get real-time updates for current move evaluation."""
        self.update_from_manager()
        
        if not self.current_move:
            return {"status": "no_active_move", "timestamp": time.time()}
        
        return {
            "status": "active",
            "timestamp": time.time(),
            "current_phase": self.current_move.current_phase.value,
            "move": self.current_move.san_notation or str(self.current_move.move),
            "agents_evaluated": len(self.current_move.bot_evaluations),
            "total_agents": self.current_move.metadata.get('total_agents', 0),
            "duration_ms": (time.time() - self.current_move.created_at) * 1000,
            "status": self.current_move.status.value,
            "confidence": self.current_move.confidence,
            "contributing_factors": self.current_move.contributing_factors
        }


# Global instance for easy access
decision_roadmap = DecisionRoadmap()


def get_current_roadmap() -> Dict[str, Any]:
    """Convenience function to get current roadmap."""
    return decision_roadmap.get_current_roadmap()


def export_roadmap(filename: str, include_history: bool = True) -> None:
    """Convenience function to export roadmap."""
    decision_roadmap.export_roadmap_json(filename, include_history)


def print_roadmap_summary(move_index: int = -1) -> None:
    """Convenience function to print roadmap summary to console."""
    print(decision_roadmap.get_console_summary(move_index))
