#!/usr/bin/env python3
"""
Visualize heatmaps using matplotlib for better visual representation.
"""

import json
import os
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

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

def create_heatmap_visualization(heatmaps, output_dir="heatmap_visualizations"):
    """Create matplotlib visualizations for heatmaps."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Chess board coordinates
    files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    ranks = ['8', '7', '6', '5', '4', '3', '2', '1']
    
    # Create individual heatmaps for each piece
    for piece_type, heatmap_data in heatmaps.items():
        if not heatmap_data or not isinstance(heatmap_data, list):
            continue
            
        # Convert to numpy array
        data = np.array(heatmap_data)
        
        if data.size == 0:
            continue
            
        # Create figure
        fig, ax = plt.subplots(figsize=(8, 8))
        
        # Create heatmap
        im = ax.imshow(data, cmap='YlOrRd', aspect='equal')
        
        # Set ticks and labels
        ax.set_xticks(range(8))
        ax.set_yticks(range(8))
        ax.set_xticklabels(files)
        ax.set_yticklabels(ranks)
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Move Count', rotation=270, labelpad=20)
        
        # Add title
        ax.set_title(f'{piece_type.capitalize()} Movement Heatmap', fontsize=16, fontweight='bold')
        
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
                           fontweight='bold')
        
        # Save individual heatmap
        output_file = output_path / f"{piece_type}_heatmap.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Saved {piece_type} heatmap to {output_file}")
    
    # Create combined heatmap
    create_combined_heatmap(heatmaps, output_path, files, ranks)

def create_combined_heatmap(heatmaps, output_path, files, ranks):
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
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Create heatmap
    im = ax.imshow(combined_data, cmap='YlOrRd', aspect='equal')
    
    # Set ticks and labels
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
    
    # Save combined heatmap
    output_file = output_path / "combined_heatmap.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Saved combined heatmap to {output_file}")

def create_subplot_visualization(heatmaps, output_dir="heatmap_visualizations"):
    """Create a subplot visualization with all piece heatmaps."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Filter valid heatmaps
    valid_heatmaps = {k: v for k, v in heatmaps.items() 
                     if v and isinstance(v, list) and len(v) > 0}
    
    if not valid_heatmaps:
        print("No valid heatmap data found")
        return
    
    # Create subplots
    n_pieces = len(valid_heatmaps)
    cols = 3
    rows = (n_pieces + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(15, 5*rows))
    if rows == 1:
        axes = [axes] if cols == 1 else axes
    else:
        axes = axes.flatten()
    
    files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    ranks = ['8', '7', '6', '5', '4', '3', '2', '1']
    
    for idx, (piece_type, heatmap_data) in enumerate(valid_heatmaps.items()):
        if idx >= len(axes):
            break
            
        ax = axes[idx]
        data = np.array(heatmap_data)
        
        # Create heatmap
        im = ax.imshow(data, cmap='YlOrRd', aspect='equal')
        
        # Set ticks and labels
        ax.set_xticks(range(8))
        ax.set_yticks(range(8))
        ax.set_xticklabels(files)
        ax.set_yticklabels(ranks)
        
        # Add title
        ax.set_title(f'{piece_type.capitalize()}', fontweight='bold')
        
        # Add grid
        ax.set_xticks(np.arange(-0.5, 8, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, 8, 1), minor=True)
        ax.grid(which="minor", color="black", linestyle='-', linewidth=0.5)
        
        # Add values on squares
        for i in range(8):
            for j in range(8):
                value = data[i, j]
                if value > 0:
                    ax.text(j, i, str(int(value)), ha="center", va="center", 
                           color="white" if value > data.max()/2 else "black",
                           fontsize=8, fontweight='bold')
    
    # Hide unused subplots
    for idx in range(len(valid_heatmaps), len(axes)):
        axes[idx].set_visible(False)
    
    plt.tight_layout()
    
    # Save subplot visualization
    output_file = output_path / "all_pieces_heatmap.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Saved all pieces heatmap to {output_file}")

def main():
    """Main function to create heatmap visualizations."""
    print("Loading heatmap data...")
    heatmaps = load_heatmap_data()
    
    if not heatmaps:
        print("No heatmap data found")
        return
    
    print(f"Found {len(heatmaps)} heatmap files: {list(heatmaps.keys())}")
    
    print("Creating individual heatmap visualizations...")
    create_heatmap_visualization(heatmaps)
    
    print("Creating subplot visualization...")
    create_subplot_visualization(heatmaps)
    
    print("Heatmap visualization completed!")

if __name__ == "__main__":
    main()