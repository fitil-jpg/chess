#!/usr/bin/env python3
"""
Interactive Heatmap Viewer.

Enhanced to support both interactive display and a headless-friendly mode
that writes the generated figures to disk when no GUI backend is available.
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import matplotlib
    import matplotlib.pyplot as plt
except ImportError as exc:  # pragma: no cover - handled at runtime
    print("Matplotlib is required to run this script. Install it with 'pip install matplotlib'.")
    raise SystemExit(1) from exc

import numpy as np

def load_heatmap_data(heatmap_dir: Path) -> dict:
    """Load heatmap data from JSON files located in ``heatmap_dir``."""
    heatmaps = {}

    if not heatmap_dir.exists() or not heatmap_dir.is_dir():
        raise FileNotFoundError(f"Heatmap directory not found: {heatmap_dir}")

    for filepath in sorted(heatmap_dir.glob("heatmap_*.json")):
        piece_type = filepath.stem.replace("heatmap_", "")
        try:
            with filepath.open("r", encoding="utf-8") as f:
                heatmaps[piece_type] = json.load(f)
        except json.JSONDecodeError as exc:
            print(f"Warning: Skipping {filepath.name} (invalid JSON: {exc})")

    return heatmaps

def create_interactive_heatmap(heatmaps):
    """Create and return a figure with individual piece heatmaps."""
    # Chess board coordinates
    files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    ranks = ['8', '7', '6', '5', '4', '3', '2', '1']
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Chess Piece Movement Heatmaps', fontsize=16, fontweight='bold')
    
    # Flatten axes for easier indexing
    axes_flat = axes.flatten()
    
    # Piece types to display
    piece_types = ['pawn', 'knight', 'bishop', 'rook', 'queen', 'king']
    
    for idx, piece_type in enumerate(piece_types):
        ax = axes_flat[idx]
        
        if piece_type in heatmaps and heatmaps[piece_type]:
            data = np.array(heatmaps[piece_type])
            
            # Create heatmap
            im = ax.imshow(data, cmap='YlOrRd', aspect='equal')
            
            # Set ticks and labels
            ax.set_xticks(range(8))
            ax.set_yticks(range(8))
            ax.set_xticklabels(files)
            ax.set_yticklabels(ranks)
            
            # Add title
            ax.set_title(f'{piece_type.capitalize()} Heatmap', fontweight='bold')
            
            # Add grid
            ax.set_xticks(np.arange(-0.5, 8, 1), minor=True)
            ax.set_yticks(np.arange(-0.5, 8, 1), minor=True)
            ax.grid(which="minor", color="black", linestyle='-', linewidth=1)
            
            # Add values on squares
            for i in range(8):
                for j in range(8):
                    value = data[i, j]
                    if value > 0:
                        ax.text(j, i, str(int(value)), ha="center", va="center", 
                               color="white" if value > data.max()/2 else "black",
                               fontweight='bold', fontsize=8)
            
            # Add colorbar
            cbar = plt.colorbar(im, ax=ax, shrink=0.8)
            cbar.set_label('Moves', rotation=270, labelpad=15)
        else:
            ax.set_title(f'{piece_type.capitalize()} - No Data', fontweight='bold')
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12, color='gray')
            ax.set_xticks([])
            ax.set_yticks([])
    
    # Hide unused subplots
    for idx in range(len(piece_types), len(axes_flat)):
        axes_flat[idx].set_visible(False)
    
    fig.tight_layout()

    return fig

def create_combined_heatmap(heatmaps):
    """Create and return a figure for the combined heatmap showing all pieces."""
    # Sum all heatmaps
    combined_data = None
    
    for piece_type, heatmap_data in heatmaps.items():
        if not heatmap_data or not isinstance(heatmap_data, list):
            continue
            
        data = np.array(heatmap_data)
        if data.size == 0:
            continue
            
        if combined_data is None:
            combined_data = data.copy()
        else:
            combined_data += data
    
    if combined_data is None:
        print("No valid heatmap data found for combined visualization")
        return
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Create heatmap
    im = ax.imshow(combined_data, cmap='YlOrRd', aspect='equal')
    
    # Set ticks and labels
    files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    ranks = ['8', '7', '6', '5', '4', '3', '2', '1']
    
    ax.set_xticks(range(8))
    ax.set_yticks(range(8))
    ax.set_xticklabels(files)
    ax.set_yticklabels(ranks)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Total Move Count', rotation=270, labelpad=20)
    
    # Add title
    ax.set_title('Combined Movement Heatmap (All Pieces)', fontsize=16, fontweight='bold')
    
    # Add grid
    ax.set_xticks(np.arange(-0.5, 8, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, 8, 1), minor=True)
    ax.grid(which="minor", color="black", linestyle='-', linewidth=1)
    
    # Add values on squares
    for i in range(8):
        for j in range(8):
            value = combined_data[i, j]
            if value > 0:
                ax.text(j, i, str(int(value)), ha="center", va="center", 
                       color="white" if value > combined_data.max()/2 else "black",
                       fontweight='bold')
    
    fig.tight_layout()

    return fig


def backend_supports_interactive() -> bool:
    """Return True if the current matplotlib backend supports interactive display."""
    backend = matplotlib.get_backend().lower()
    headless_backends = {
        "agg", "cairoagg", "svg", "pdf", "ps", "template"
    }

    if backend in headless_backends:
        return False

    # Heuristic: on Linux-like systems require a display variable
    if sys.platform.startswith("linux"):
        if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            return False

    return True

def main():
    """Main entry point for the heatmap viewer."""
    parser = argparse.ArgumentParser(description="Display or export chess piece heatmaps.")
    parser.add_argument(
        "--heatmap-dir",
        type=Path,
        default=Path("."),
        help="Directory containing heatmap_*.json files (default: current directory)."
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "show", "save"],
        default="auto",
        help="Display figures, save them, or auto-detect the best option."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory to write generated images when saving. Default: ./heatmap_visualizations"
    )

    args = parser.parse_args()

    try:
        print("Loading heatmap data...")
        heatmaps = load_heatmap_data(args.heatmap_dir)
    except FileNotFoundError as exc:
        print(str(exc))
        return

    if not heatmaps:
        print("No heatmap data found")
        return

    print(f"Found {len(heatmaps)} heatmap files: {sorted(heatmaps.keys())}")

    interactive_available = backend_supports_interactive()
    requested_mode = args.mode

    if requested_mode == "auto":
        mode = "show" if interactive_available else "save"
    elif requested_mode == "show" and not interactive_available:
        print(
            "Interactive display backend not available (backend="
            f"{matplotlib.get_backend()}). Falling back to saving images."
        )
        mode = "save"
    else:
        mode = requested_mode

    print("\n1. Generating individual piece heatmaps...")
    individual_fig = create_interactive_heatmap(heatmaps)
    print("\n2. Generating combined heatmap...")
    combined_fig = create_combined_heatmap(heatmaps)

    figs = [("heatmap_individual.png", individual_fig), ("heatmap_combined.png", combined_fig)]

    if mode == "save":
        output_dir = args.output_dir or (args.heatmap_dir / "heatmap_visualizations")
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_paths = []
        for filename, fig in figs:
            if fig is None:
                continue
            target = output_dir / filename
            fig.savefig(target, dpi=200)
            saved_paths.append(target)
            plt.close(fig)

        if saved_paths:
            print("Saved heatmap images:")
            for path in saved_paths:
                print(f"  - {path}")
        else:
            print("No figures to save.")

        print("\nHeatmap generation completed (saved to disk).")
    else:  # mode == "show"
        print("\nDisplaying heatmaps in interactive windows...")
        plt.show()
        print("\nHeatmap visualization completed!")

if __name__ == "__main__":
    main()