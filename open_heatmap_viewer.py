#!/usr/bin/env python3
"""
Open the interactive heatmap viewer in the default browser
"""

import webbrowser
import os
from pathlib import Path

def main():
    """Open the heatmap viewer in browser."""
    # Get the absolute path to the HTML file
    html_file = Path(__file__).parent / "heatmap_web_interface.html"
    
    if not html_file.exists():
        print(f"Error: {html_file} not found!")
        return
    
    # Convert to file:// URL
    file_url = f"file://{html_file.absolute()}"
    
    print(f"Opening heatmap viewer: {file_url}")
    print("If the browser doesn't open automatically, copy the URL above to your browser.")
    
    # Try to open in browser
    try:
        webbrowser.open(file_url)
        print("✅ Heatmap viewer opened in browser!")
    except Exception as e:
        print(f"❌ Could not open browser automatically: {e}")
        print(f"Please open this URL manually: {file_url}")

if __name__ == "__main__":
    main()