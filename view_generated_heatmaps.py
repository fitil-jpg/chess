#!/usr/bin/env python3
"""
View generated heatmap PNG files
"""

import os
import webbrowser
from pathlib import Path

def main():
    """Open the generated heatmap images."""
    heatmap_dir = Path("heatmap_visualizations")
    
    if not heatmap_dir.exists():
        print("❌ Heatmap visualizations directory not found!")
        print("Run visualize_heatmap_matplotlib.py first to generate images.")
        return
    
    # List all PNG files
    png_files = list(heatmap_dir.glob("*.png"))
    
    if not png_files:
        print("❌ No PNG files found in heatmap_visualizations directory!")
        return
    
    print("📊 Generated Heatmap Images:")
    print("=" * 50)
    
    for i, png_file in enumerate(png_files, 1):
        print(f"{i}. {png_file.name}")
    
    print("\n🔍 Opening images in default viewer...")
    
    # Open each image
    for png_file in png_files:
        try:
            file_url = f"file://{png_file.absolute()}"
            webbrowser.open(file_url)
            print(f"✅ Opened: {png_file.name}")
        except Exception as e:
            print(f"❌ Could not open {png_file.name}: {e}")
    
    print(f"\n📁 All images are located in: {heatmap_dir.absolute()}")
    print("You can also view them manually by opening the heatmap_visualizations folder.")

if __name__ == "__main__":
    main()