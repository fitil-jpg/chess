#!/usr/bin/env python3
"""
Interactive Heatmap Viewer - показує heatmap в інтерактивному вікні
"""

import json
import os
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import matplotlib.patches as patches

def load_heatmap_data(heatmap_dir="."):
    """Load heatmap data from JSON files."""
    heatmaps = {}
    
    for filename in os.listdir(heatmap_dir):
        if filename.startswith("heatmap_") and filename.endswith(".json"):
            piece_type = filename.replace("heatmap_", "").replace(".json", "")
            filepath = os.path.join(heatmap_dir, filename)
            
            with open(filepath, 'r') as f:
                heatmaps[piece_type] = json.load(f)
    
    return heatmaps

def create_interactive_heatmap(heatmaps):
    """Create an interactive heatmap viewer."""
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
    
    plt.tight_layout()
    
    # Show the plot
    plt.show()

def create_combined_heatmap(heatmaps):
    """Create a combined heatmap showing all pieces."""
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
    
    plt.tight_layout()
    plt.show()

def main():
    """Main function to create interactive heatmap visualizations."""
    print("Loading heatmap data...")
    heatmaps = load_heatmap_data()
    
    if not heatmaps:
        print("No heatmap data found")
        return
    
    print(f"Found {len(heatmaps)} heatmap files: {list(heatmaps.keys())}")
    
    print("\n1. Showing individual piece heatmaps...")
    create_interactive_heatmap(heatmaps)
    
    print("\n2. Showing combined heatmap...")
    create_combined_heatmap(heatmaps)
    
    print("\nHeatmap visualization completed!")

if __name__ == "__main__":
    main()