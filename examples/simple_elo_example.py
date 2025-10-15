#!/usr/bin/env python3
"""
Simple example of ELO synchronization without web interface.

This example shows how to use the simplified ELO sync system
to keep your chess bots' ratings synchronized with external platforms.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from chess_ai.simple_elo_sync import SimpleELOSync


async def example_basic_usage():
    """Basic usage example."""
    print("=== Basic ELO Sync Usage ===\n")
    
    # Initialize sync system
    sync_system = SimpleELOSync(
        lichess_token=os.getenv('LICHESS_TOKEN'),
        chesscom_username=os.getenv('CHESSCOM_USERNAME'),
        chesscom_password=os.getenv('CHESSCOM_PASSWORD'),
        ratings_file="example_ratings.json"
    )
    
    # 1. Register bots
    print("1. Registering bots...")
    bot_configs = {
        "DynamicBot": 1500.0,
        "StockfishBot": 2000.0,
        "FortifyBot": 1400.0,
        "AggressiveBot": 1600.0
    }
    register_results = sync_system.register_bots(bot_configs)
    print("Register results:")
    print(json.dumps(register_results, indent=2))
    
    # 2. Set platform mappings
    print("\n2. Setting platform mappings...")
    mappings = {
        "lichess": {
            "DynamicBot": "your_lichess_dynamic_bot",
            "StockfishBot": "your_lichess_stockfish_bot"
        },
        "chesscom": {
            "DynamicBot": "your_chesscom_dynamic_bot",
            "StockfishBot": "your_chesscom_stockfish_bot"
        }
    }
    mapping_results = sync_system.set_platform_mappings(mappings)
    print("Mapping results:")
    print(json.dumps(mapping_results, indent=2))
    
    # 3. Sync ratings
    print("\n3. Syncing ratings...")
    bot_names = ["DynamicBot", "StockfishBot"]
    sync_results = await sync_system.sync_ratings(bot_names, ["lichess", "chesscom"])
    print("Sync results:")
    print(json.dumps(sync_results, indent=2))
    
    # 4. Get current ratings
    print("\n4. Current ratings:")
    summary = sync_system.get_ratings_summary()
    print(json.dumps(summary, indent=2))
    
    # 5. Export ratings
    print("\n5. Exporting ratings...")
    exported = sync_system.export_ratings("json")
    print("Exported ratings:")
    print(exported)


async def example_scheduler_usage():
    """Scheduler usage example."""
    print("\n=== Scheduler Usage Example ===\n")
    
    sync_system = SimpleELOSync(
        lichess_token=os.getenv('LICHESS_TOKEN'),
        chesscom_username=os.getenv('CHESSCOM_USERNAME'),
        chesscom_password=os.getenv('CHESSCOM_PASSWORD'),
        ratings_file="example_ratings.json"
    )
    
    # Setup scheduler configurations
    configs = {
        "frequent_sync": {
            "bot_names": ["DynamicBot", "StockfishBot"],
            "platforms": ["lichess"],
            "interval_minutes": 30,
            "enabled": True
        },
        "regular_sync": {
            "bot_names": ["FortifyBot", "AggressiveBot"],
            "platforms": ["lichess", "chesscom"],
            "interval_minutes": 120,
            "enabled": False  # Disabled for example
        }
    }
    
    print("Setting up scheduler...")
    setup_results = sync_system.setup_scheduler(configs)
    print("Scheduler setup results:")
    print(json.dumps(setup_results, indent=2))
    
    # Get scheduler status
    print("\nScheduler status:")
    status = sync_system.get_scheduler_status()
    print(json.dumps(status, indent=2))
    
    # Note: In a real application, you would start the scheduler
    # await sync_system.start_scheduler()


async def example_manual_updates():
    """Manual rating updates example."""
    print("\n=== Manual Rating Updates Example ===\n")
    
    sync_system = SimpleELOSync(ratings_file="example_ratings.json")
    
    # Register a bot
    sync_system.register_bots({"TestBot": 1500.0})
    
    # Get initial rating
    print("Initial rating:")
    rating = sync_system.get_bot_rating("TestBot")
    print(json.dumps(rating, indent=2))
    
    # Update rating manually
    print("\nUpdating rating manually...")
    success = sync_system.update_bot_rating("TestBot", 1600.0, "Manual update after win")
    print(f"Update successful: {success}")
    
    # Get updated rating
    print("\nUpdated rating:")
    rating = sync_system.get_bot_rating("TestBot")
    print(json.dumps(rating, indent=2))


def example_cli_usage():
    """CLI usage example."""
    print("\n=== CLI Usage Examples ===\n")
    
    print("1. Register a bot:")
    print("   python scripts/simple_elo_sync.py register MyBot --initial-elo 1500")
    
    print("\n2. Set platform mapping:")
    print("   python scripts/simple_elo_sync.py mapping set lichess MyBot my_lichess_bot")
    
    print("\n3. Sync ratings:")
    print("   python scripts/simple_elo_sync.py sync MyBot --platforms lichess")
    
    print("\n4. List all ratings:")
    print("   python scripts/simple_elo_sync.py list")
    
    print("\n5. List specific bot:")
    print("   python scripts/simple_elo_sync.py list --bot MyBot")
    
    print("\n6. Quiet mode (JSON only):")
    print("   python scripts/simple_elo_sync.py list --quiet")


async def main():
    """Main example function."""
    print("ELO Synchronization Examples")
    print("=" * 50)
    
    # Set environment variables for testing
    os.environ.setdefault('LICHESS_TOKEN', '')
    os.environ.setdefault('CHESSCOM_USERNAME', '')
    os.environ.setdefault('CHESSCOM_PASSWORD', '')
    
    try:
        await example_basic_usage()
        await example_scheduler_usage()
        await example_manual_updates()
        example_cli_usage()
        
        print("\n" + "=" * 50)
        print("Examples completed successfully!")
        print("\nNote: Chess.com API is read-only - it can only fetch ratings,")
        print("not play games. For playing games, use Lichess API.")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        print("Make sure you have set up your API credentials in environment variables.")


if __name__ == "__main__":
    asyncio.run(main())