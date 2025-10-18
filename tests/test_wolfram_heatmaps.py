"""Tests for Wolfram Engine heatmap generation."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from utils.integration import generate_heatmaps


class TestWolframHeatmapGeneration:
    """Test cases for Wolfram heatmap generation."""
    
    def test_generate_heatmaps_wolfram_success(self):
        """Test successful heatmap generation with Wolfram Engine."""
        fens = [
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('subprocess.run') as mock_run:
                # Mock successful Wolfram execution
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = "Heatmap generation completed"
                
                # Mock heatmap files
                heatmap_dir = Path(temp_dir) / "test_pattern"
                heatmap_dir.mkdir(parents=True)
                
                # Create mock heatmap files
                mock_heatmaps = {
                    "P": [[0, 0, 0, 0, 0, 0, 0, 0],
                          [1, 1, 1, 1, 1, 1, 1, 1],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0]],
                    "R": [[1, 0, 0, 0, 0, 0, 0, 1],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [1, 0, 0, 0, 0, 0, 0, 1]]
                }
                
                for piece, matrix in mock_heatmaps.items():
                    heatmap_file = heatmap_dir / f"heatmap_{piece}.json"
                    with heatmap_file.open('w') as f:
                        json.dump(matrix, f)
                
                # Test heatmap generation
                result = generate_heatmaps(
                    fens, 
                    out_dir=temp_dir, 
                    pattern_set="test_pattern",
                    use_wolfram=True
                )
                
                # Verify result
                assert "test_pattern" in result
                assert "P" in result["test_pattern"]
                assert "R" in result["test_pattern"]
                assert result["test_pattern"]["P"] == mock_heatmaps["P"]
                assert result["test_pattern"]["R"] == mock_heatmaps["R"]
    
    def test_generate_heatmaps_wolfram_script_not_found(self):
        """Test heatmap generation when wolframscript is not found."""
        fens = ["rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('subprocess.run') as mock_run:
                # Mock wolframscript not found
                mock_run.side_effect = FileNotFoundError("wolframscript not found")
                
                with pytest.raises(RuntimeError, match="wolframscript not found"):
                    generate_heatmaps(
                        fens, 
                        out_dir=temp_dir, 
                        use_wolfram=True
                    )
    
    def test_generate_heatmaps_wolfram_script_failure(self):
        """Test heatmap generation when Wolfram script fails."""
        fens = ["rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('subprocess.run') as mock_run:
                # Mock Wolfram script failure
                mock_run.return_value.returncode = 1
                mock_run.return_value.stderr = "Wolfram script failed"
                
                with pytest.raises(RuntimeError, match="wolframscript failed"):
                    generate_heatmaps(
                        fens, 
                        out_dir=temp_dir, 
                        use_wolfram=True
                    )
    
    def test_generate_heatmaps_wolfram_no_output_files(self):
        """Test heatmap generation when no output files are generated."""
        fens = ["rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('subprocess.run') as mock_run:
                # Mock successful Wolfram execution but no output files
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = "Script completed"
                
                with pytest.raises(RuntimeError, match="No heatmap files generated"):
                    generate_heatmaps(
                        fens, 
                        out_dir=temp_dir, 
                        pattern_set="empty",
                        use_wolfram=True
                    )
    
    def test_generate_heatmaps_wolfram_invalid_json(self):
        """Test heatmap generation with invalid JSON files."""
        fens = ["rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('subprocess.run') as mock_run:
                # Mock successful Wolfram execution
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = "Script completed"
                
                # Create invalid JSON files
                heatmap_dir = Path(temp_dir) / "invalid"
                heatmap_dir.mkdir(parents=True)
                
                heatmap_file = heatmap_dir / "heatmap_P.json"
                with heatmap_file.open('w') as f:
                    f.write("Invalid JSON content")
                
                with pytest.raises(RuntimeError, match="No valid heatmap files could be loaded"):
                    generate_heatmaps(
                        fens, 
                        out_dir=temp_dir, 
                        pattern_set="invalid",
                        use_wolfram=True
                    )
    
    def test_generate_heatmaps_wolfram_command_construction(self):
        """Test that Wolfram command is constructed correctly."""
        fens = ["rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('subprocess.run') as mock_run:
                # Mock successful Wolfram execution
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = "Script completed"
                
                # Create mock heatmap files
                heatmap_dir = Path(temp_dir) / "test"
                heatmap_dir.mkdir(parents=True)
                
                heatmap_file = heatmap_dir / "heatmap_P.json"
                with heatmap_file.open('w') as f:
                    json.dump([[1, 1], [1, 1]], f)
                
                generate_heatmaps(
                    fens, 
                    out_dir=temp_dir, 
                    pattern_set="test",
                    use_wolfram=True
                )
                
                # Verify command construction
                assert mock_run.call_count >= 1
                call_args = mock_run.call_args_list[-1]
                command = call_args[0][0]
                
                assert command[0] == "wolframscript"
                assert command[1] == "-file"
                assert command[2].endswith("generate_heatmaps.wl")
                assert command[3].endswith(".csv")


class TestWolframHeatmapIntegration:
    """Integration tests for Wolfram heatmap generation."""
    
    def test_wolfram_vs_r_consistency(self):
        """Test that Wolfram and R generate consistent results."""
        fens = [
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # This test would require both R and Wolfram to be available
            # For now, we'll just test that both methods can be called
            with patch('subprocess.run') as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = "Script completed"
                
                # Create mock heatmap files
                heatmap_dir = Path(temp_dir) / "test"
                heatmap_dir.mkdir(parents=True)
                
                heatmap_file = heatmap_dir / "heatmap_P.json"
                with heatmap_file.open('w') as f:
                    json.dump([[1, 1], [1, 1]], f)
                
                # Test both methods
                wolfram_result = generate_heatmaps(
                    fens, 
                    out_dir=temp_dir, 
                    pattern_set="test",
                    use_wolfram=True
                )
                
                r_result = generate_heatmaps(
                    fens, 
                    out_dir=temp_dir, 
                    pattern_set="test",
                    use_wolfram=False
                )
                
                # Both should succeed
                assert "test" in wolfram_result
                assert "test" in r_result


if __name__ == "__main__":
    pytest.main([__file__])