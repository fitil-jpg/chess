#!/usr/bin/env python3
"""
XRPA (X-Ray Position Analysis) Analyzer

This script analyzes saved PNG images and JSON data from chess games
to provide insights for position analysis.
"""

import json
import os
import glob
from pathlib import Path
from datetime import datetime
import argparse

def analyze_xrpa_data(xrpa_dir="xrpa_analysis"):
    """Analyze all XRPA data files in the specified directory."""
    
    if not os.path.exists(xrpa_dir):
        print(f"XRPA directory not found: {xrpa_dir}")
        return
    
    # Find all JSON data files
    json_files = glob.glob(os.path.join(xrpa_dir, "*_data.json"))
    
    if not json_files:
        print(f"No XRPA data files found in {xrpa_dir}")
        return
    
    print(f"Found {len(json_files)} XRPA analysis files")
    print("=" * 60)
    
    # Analyze each file
    for json_file in sorted(json_files):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract basic info
            timestamp = data.get('timestamp', 'Unknown')
            result = data.get('result', 'Unknown')
            move_count = data.get('move_count', 0)
            white_agent = data.get('white_agent', 'Unknown')
            black_agent = data.get('black_agent', 'Unknown')
            fen = data.get('fen', '')
            heatmap_piece = data.get('heatmap_piece')
            
            print(f"\n📊 Analysis: {os.path.basename(json_file)}")
            print(f"   Time: {timestamp}")
            print(f"   Result: {result}")
            print(f"   Moves: {move_count}")
            print(f"   Players: {white_agent} vs {black_agent}")
            print(f"   Heatmap: {heatmap_piece or 'None'}")
            print(f"   FEN: {fen[:50]}...")
            
            # Analyze heatmaps if available
            if 'heatmaps' in data and data['heatmaps']:
                print(f"   Available heatmaps: {list(data['heatmaps'].keys())}")
                
                # Analyze active heatmap
                if heatmap_piece and heatmap_piece in data['heatmaps']:
                    heatmap_data = data['heatmaps'][heatmap_piece]
                    if isinstance(heatmap_data, list) and len(heatmap_data) == 8:
                        # Calculate heatmap statistics
                        all_values = []
                        for row in heatmap_data:
                            if isinstance(row, list):
                                all_values.extend(row)
                        
                        if all_values:
                            max_val = max(all_values)
                            min_val = min(all_values)
                            avg_val = sum(all_values) / len(all_values)
                            
                            print(f"   Heatmap stats: max={max_val:.3f}, min={min_val:.3f}, avg={avg_val:.3f}")
            
            # Analyze overlays if available
            if 'overlays' in data and data['overlays']:
                overlay_count = 0
                overlay_types = set()
                for row in data['overlays']:
                    for cell in row:
                        if cell:  # Non-empty cell
                            overlay_count += 1
                            for overlay_type, _ in cell:
                                overlay_types.add(overlay_type)
                
                print(f"   Overlays: {overlay_count} cells, types: {sorted(overlay_types)}")
            
            # Analyze scenarios if available
            if 'scenarios' in data and data['scenarios']:
                print(f"   Scenarios detected: {len(data['scenarios'])}")
                for i, scenario in enumerate(data['scenarios'][:3]):  # Show first 3
                    print(f"     {i+1}. {scenario.get('type', 'Unknown')} at {scenario.get('square', 'Unknown')}")
            
        except Exception as e:
            print(f"Error analyzing {json_file}: {e}")

def generate_xrpa_report(xrpa_dir="xrpa_analysis", output_file="xrpa_report.html"):
    """Generate an HTML report of XRPA analysis."""
    
    json_files = glob.glob(os.path.join(xrpa_dir, "*_data.json"))
    
    if not json_files:
        print(f"No XRPA data files found in {xrpa_dir}")
        return
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>XRPA Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .game {{ border: 1px solid #ccc; margin: 10px 0; padding: 15px; }}
            .header {{ background-color: #f0f0f0; padding: 10px; font-weight: bold; }}
            .info {{ margin: 5px 0; }}
            .heatmap {{ background-color: #e8f4f8; padding: 10px; margin: 5px 0; }}
            .overlay {{ background-color: #f8f8e8; padding: 10px; margin: 5px 0; }}
        </style>
    </head>
    <body>
        <h1>XRPA (X-Ray Position Analysis) Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Total games analyzed: {len(json_files)}</p>
    """
    
    for json_file in sorted(json_files):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            timestamp = data.get('timestamp', 'Unknown')
            result = data.get('result', 'Unknown')
            move_count = data.get('move_count', 0)
            white_agent = data.get('white_agent', 'Unknown')
            black_agent = data.get('black_agent', 'Unknown')
            fen = data.get('fen', '')
            heatmap_piece = data.get('heatmap_piece')
            
            # Find corresponding PNG file
            png_file = json_file.replace('_data.json', '.png')
            png_exists = os.path.exists(png_file)
            
            html_content += f"""
            <div class="game">
                <div class="header">
                    Game Analysis - {os.path.basename(json_file)}
                </div>
                <div class="info"><strong>Time:</strong> {timestamp}</div>
                <div class="info"><strong>Result:</strong> {result}</div>
                <div class="info"><strong>Moves:</strong> {move_count}</div>
                <div class="info"><strong>Players:</strong> {white_agent} vs {black_agent}</div>
                <div class="info"><strong>FEN:</strong> {fen}</div>
            """
            
            if png_exists:
                html_content += f'<div class="info"><strong>Board Image:</strong> <img src="{os.path.basename(png_file)}" style="max-width: 400px;"></div>'
            
            if heatmap_piece:
                html_content += f'<div class="heatmap"><strong>Active Heatmap:</strong> {heatmap_piece}</div>'
            
            if 'heatmaps' in data and data['heatmaps']:
                html_content += f'<div class="heatmap"><strong>Available Heatmaps:</strong> {", ".join(data["heatmaps"].keys())}</div>'
            
            if 'overlays' in data and data['overlays']:
                overlay_count = sum(1 for row in data['overlays'] for cell in row if cell)
                html_content += f'<div class="overlay"><strong>Overlays:</strong> {overlay_count} cells with overlays</div>'
            
            if 'scenarios' in data and data['scenarios']:
                html_content += f'<div class="overlay"><strong>Scenarios:</strong> {len(data["scenarios"])} detected</div>'
            
            html_content += "</div>"
            
        except Exception as e:
            html_content += f'<div class="game"><div class="header">Error analyzing {json_file}</div><div class="info">Error: {e}</div></div>'
    
    html_content += """
    </body>
    </html>
    """
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"XRPA report generated: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="XRPA Analysis Tool")
    parser.add_argument("--dir", default="xrpa_analysis", help="XRPA data directory")
    parser.add_argument("--report", action="store_true", help="Generate HTML report")
    parser.add_argument("--output", default="xrpa_report.html", help="Output HTML file")
    
    args = parser.parse_args()
    
    if args.report:
        generate_xrpa_report(args.dir, args.output)
    else:
        analyze_xrpa_data(args.dir)

if __name__ == "__main__":
    main()
