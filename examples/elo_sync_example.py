#!/usr/bin/env python3
"""
Example usage of the ELO synchronization system.

This script demonstrates how to use the ELO sync manager and scheduler
to keep your chess bots' ratings synchronized with external platforms.
"""

import asyncio
import logging
import os
from pathlib import Path

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from chess_ai.elo_sync_manager import ELOSyncManager, ELOPlatform
from chess_ai.elo_scheduler import ELOScheduler, SyncConfig, console_notification

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Example usage of ELO synchronization."""
    
    # Initialize the ELO sync manager
    # In production, you would load these from environment variables
    manager = ELOSyncManager(
        lichess_token=os.getenv('LICHESS_TOKEN'),
        chesscom_username=os.getenv('CHESSCOM_USERNAME'),
        chesscom_password=os.getenv('CHESSCOM_PASSWORD')
    )
    
    # Register your bots
    bot_names = ["DynamicBot", "StockfishBot", "FortifyBot", "AggressiveBot"]
    
    for bot_name in bot_names:
        manager.register_bot(bot_name, initial_elo=1500.0)
        logger.info(f"Registered bot: {bot_name}")
    
    # Set up platform mappings
    # Replace with your actual platform usernames
    lichess_mappings = {
        "DynamicBot": "your_lichess_dynamic_bot",
        "StockfishBot": "your_lichess_stockfish_bot",
        "FortifyBot": "your_lichess_fortify_bot",
        "AggressiveBot": "your_lichess_aggressive_bot"
    }
    
    chesscom_mappings = {
        "DynamicBot": "your_chesscom_dynamic_bot",
        "StockfishBot": "your_chesscom_stockfish_bot",
        "FortifyBot": "your_chesscom_fortify_bot",
        "AggressiveBot": "your_chesscom_aggressive_bot"
    }
    
    # Set platform mappings
    for bot_name, lichess_username in lichess_mappings.items():
        manager.set_platform_mapping(ELOPlatform.LICHESS, bot_name, lichess_username)
        logger.info(f"Set Lichess mapping: {bot_name} → {lichess_username}")
    
    for bot_name, chesscom_username in chesscom_mappings.items():
        manager.set_platform_mapping(ELOPlatform.CHESSCOM, bot_name, chesscom_username)
        logger.info(f"Set Chess.com mapping: {bot_name} → {chesscom_username}")
    
    # Initialize scheduler
    scheduler = ELOScheduler(manager)
    
    # Add notification callback
    scheduler.add_notification_callback(console_notification)
    
    # Create sync configurations
    # Frequent sync for active bots
    frequent_config = SyncConfig(
        bot_names=["DynamicBot", "StockfishBot"],
        platforms=[ELOPlatform.LICHESS, ELOPlatform.CHESSCOM],
        interval_minutes=30,  # Every 30 minutes
        enabled=True
    )
    scheduler.add_config("frequent_sync", frequent_config)
    
    # Less frequent sync for other bots
    regular_config = SyncConfig(
        bot_names=["FortifyBot", "AggressiveBot"],
        platforms=[ELOPlatform.LICHESS],
        interval_minutes=120,  # Every 2 hours
        enabled=True
    )
    scheduler.add_config("regular_sync", regular_config)
    
    # Manual sync example
    logger.info("Performing manual sync...")
    try:
        results = await manager.sync_all_platforms(bot_names)
        
        for platform, platform_results in results.items():
            logger.info(f"\n{platform.upper()} Results:")
            for result in platform_results:
                if result.success:
                    logger.info(f"  {result.bot_name}: {result.old_elo:.1f} → {result.new_elo:.1f} "
                              f"(+{result.rating_change:.1f})")
                else:
                    logger.error(f"  {result.bot_name}: ERROR - {result.error}")
    except Exception as e:
        logger.error(f"Manual sync failed: {e}")
    
    # Display current ratings
    logger.info("\nCurrent Bot Ratings:")
    summary = manager.get_rating_summary()
    for bot_name, bot_data in summary["bots"].items():
        logger.info(f"  {bot_name}: {bot_data['elo']:.1f} ELO "
                   f"({bot_data['games_played']} games)")
    
    # Start automated scheduler (uncomment to run continuously)
    # logger.info("Starting automated scheduler...")
    # await scheduler.start()
    
    # Example of updating a bot's rating manually
    logger.info("\nExample: Updating DynamicBot rating manually...")
    manager.update_bot_rating("DynamicBot", 1600.0, ELOPlatform.LOCAL, "Manual update")
    
    # Export ratings
    logger.info("\nExporting ratings...")
    json_export = manager.export_ratings("json")
    logger.info("JSON export:")
    logger.info(json_export[:200] + "..." if len(json_export) > 200 else json_export)
    
    # Get scheduler status
    if scheduler:
        status = scheduler.get_status()
        logger.info(f"\nScheduler Status:")
        logger.info(f"  Running: {status['running']}")
        logger.info(f"  Configurations: {status['configurations']}")
        logger.info(f"  Enabled: {status['enabled_configurations']}")


if __name__ == "__main__":
    # Set environment variables for testing (in production, use .env file)
    os.environ.setdefault('LICHESS_TOKEN', '')
    os.environ.setdefault('CHESSCOM_USERNAME', '')
    os.environ.setdefault('CHESSCOM_PASSWORD', '')
    
    asyncio.run(main())