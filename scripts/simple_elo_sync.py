#!/usr/bin/env python3
"""
Simple ELO synchronization script without web interface.

This script provides a simple way to sync ELO ratings from external platforms
and output results in JSON format for easy parsing.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from chess_ai.simple_elo_sync import SimpleELOSync, print_json


async def main():
    """Main function demonstrating ELO sync usage."""
    
    # Load configuration from environment
    lichess_token = os.getenv('LICHESS_TOKEN')
    chesscom_username = os.getenv('CHESSCOM_USERNAME')
    chesscom_password = os.getenv('CHESSCOM_PASSWORD')
    
    # Initialize sync system
    sync_system = SimpleELOSync(
        lichess_token=lichess_token,
        chesscom_username=chesscom_username,
        chesscom_password=chesscom_password,
        ratings_file="ratings.json"
    )
    
    # Register your bots
    bot_configs = {
        "DynamicBot": 1500.0,
        "StockfishBot": 2000.0,
        "FortifyBot": 1400.0,
        "AggressiveBot": 1600.0
    }
    
    print("Registering bots...")
    register_results = sync_system.register_bots(bot_configs)
    print_json(register_results)
    
    # Set platform mappings (replace with your actual usernames)
    mappings = {
        "lichess": {
            "DynamicBot": "your_lichess_dynamic_bot",
            "StockfishBot": "your_lichess_stockfish_bot",
            "FortifyBot": "your_lichess_fortify_bot",
            "AggressiveBot": "your_lichess_aggressive_bot"
        },
        "chesscom": {
            "DynamicBot": "your_chesscom_dynamic_bot",
            "StockfishBot": "your_chesscom_stockfish_bot",
            "FortifyBot": "your_chesscom_fortify_bot",
            "AggressiveBot": "your_chesscom_aggressive_bot"
        }
    }
    
    print("\nSetting platform mappings...")
    mapping_results = sync_system.set_platform_mappings(mappings)
    print_json(mapping_results)
    
    # Sync ratings from platforms
    print("\nSyncing ratings from platforms...")
    bot_names = list(bot_configs.keys())
    sync_results = await sync_system.sync_ratings(bot_names, ["lichess", "chesscom"])
    print_json(sync_results)
    
    # Show current ratings
    print("\nCurrent ratings summary:")
    summary = sync_system.get_ratings_summary()
    print_json(summary)
    
    # Export ratings
    print("\nExporting ratings...")
    exported = sync_system.export_ratings("json")
    print("Exported ratings:")
    print(exported)


if __name__ == "__main__":
    asyncio.run(main())