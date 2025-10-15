#!/usr/bin/env python3
"""
Command-line interface for ELO synchronization management.

This script provides a CLI for managing ELO synchronization without
needing to use the web interface or write custom code.
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from chess_ai.elo_sync_manager import ELOSyncManager, ELOPlatform
from chess_ai.elo_scheduler import ELOScheduler, SyncConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from environment variables."""
    import os
    return {
        'lichess_token': os.getenv('LICHESS_TOKEN'),
        'chesscom_username': os.getenv('CHESSCOM_USERNAME'),
        'chesscom_password': os.getenv('CHESSCOM_PASSWORD'),
        'ratings_file': os.getenv('RATINGS_FILE', 'ratings.json'),
        'config_file': os.getenv('CONFIG_FILE', 'sync_config.json')
    }


async def cmd_sync(args):
    """Sync ratings from platforms."""
    config = load_config()
    manager = ELOSyncManager(
        ratings_file=config['ratings_file'],
        lichess_token=config['lichess_token'],
        chesscom_username=config['chesscom_username'],
        chesscom_password=config['chesscom_password']
    )
    
    if args.platform == 'all':
        results = await manager.sync_all_platforms(args.bots)
    else:
        results = await manager.sync_platform(args.platform, args.bots)
    
    # Print results
    if isinstance(results, dict):
        for platform, platform_results in results.items():
            print(f"\n{platform.upper()} Results:")
            for result in platform_results:
                if result.success:
                    print(f"  ✅ {result.bot_name}: {result.old_elo:.1f} → {result.new_elo:.1f} "
                          f"(+{result.rating_change:.1f})")
                else:
                    print(f"  ❌ {result.bot_name}: {result.error}")
    else:
        for result in results:
            if result.success:
                print(f"  ✅ {result.bot_name}: {result.old_elo:.1f} → {result.new_elo:.1f} "
                      f"(+{result.rating_change:.1f})")
            else:
                print(f"  ❌ {result.bot_name}: {result.error}")


async def cmd_list(args):
    """List bot ratings."""
    config = load_config()
    manager = ELOSyncManager(
        ratings_file=config['ratings_file'],
        lichess_token=config['lichess_token'],
        chesscom_username=config['chesscom_username'],
        chesscom_password=config['chesscom_password']
    )
    
    summary = manager.get_rating_summary()
    
    if args.bot:
        if args.bot in summary['bots']:
            bot_data = summary['bots'][args.bot]
            print(f"\n{args.bot}:")
            print(f"  ELO: {bot_data['elo']:.1f}")
            print(f"  Games: {bot_data['games_played']}")
            print(f"  Last Updated: {bot_data['last_updated']}")
            print(f"  Confidence: {bot_data['confidence']:.2f}")
            if bot_data['platform_ratings']:
                print(f"  Platform Ratings:")
                for platform, rating_data in bot_data['platform_ratings'].items():
                    print(f"    {platform}: {rating_data['rating']:.1f}")
        else:
            print(f"Bot '{args.bot}' not found")
    else:
        print(f"\nBot Ratings (Total: {summary['total_bots']}):")
        print(f"{'Bot Name':<15} {'ELO':<8} {'Games':<6} {'Last Updated':<20}")
        print("-" * 60)
        
        for bot_name, bot_data in summary['bots'].items():
            print(f"{bot_name:<15} {bot_data['elo']:<8.1f} {bot_data['games_played']:<6} "
                  f"{bot_data['last_updated'][:19]}")


async def cmd_register(args):
    """Register a new bot."""
    config = load_config()
    manager = ELOSyncManager(
        ratings_file=config['ratings_file'],
        lichess_token=config['lichess_token'],
        chesscom_username=config['chesscom_username'],
        chesscom_password=config['chesscom_password']
    )
    
    success = manager.register_bot(args.name, args.initial_elo)
    if success:
        print(f"✅ Registered bot '{args.name}' with ELO {args.initial_elo}")
    else:
        print(f"❌ Failed to register bot '{args.name}' (may already exist)")


async def cmd_mapping(args):
    """Manage platform mappings."""
    config = load_config()
    manager = ELOSyncManager(
        ratings_file=config['ratings_file'],
        lichess_token=config['lichess_token'],
        chesscom_username=config['chesscom_username'],
        chesscom_password=config['chesscom_password']
    )
    
    if args.action == 'set':
        platform_map = {
            'lichess': ELOPlatform.LICHESS,
            'chesscom': ELOPlatform.CHESSCOM
        }
        
        if args.platform not in platform_map:
            print(f"❌ Unknown platform: {args.platform}")
            return
        
        success = manager.set_platform_mapping(
            platform_map[args.platform], 
            args.bot_name, 
            args.platform_username
        )
        
        if success:
            print(f"✅ Set {args.platform} mapping: {args.bot_name} → {args.platform_username}")
        else:
            print(f"❌ Failed to set mapping")
    
    elif args.action == 'list':
        lichess_mapping = manager.get_bot_lichess_mapping()
        chesscom_mapping = manager.get_bot_chesscom_mapping()
        
        print("\nPlatform Mappings:")
        print(f"{'Bot Name':<15} {'Lichess':<20} {'Chess.com':<20}")
        print("-" * 60)
        
        all_bots = set(lichess_mapping.keys()) | set(chesscom_mapping.keys())
        for bot_name in sorted(all_bots):
            lichess_user = lichess_mapping.get(bot_name, '-')
            chesscom_user = chesscom_mapping.get(bot_name, '-')
            print(f"{bot_name:<15} {lichess_user:<20} {chesscom_user:<20}")


async def cmd_scheduler(args):
    """Manage scheduler."""
    config = load_config()
    manager = ELOSyncManager(
        ratings_file=config['ratings_file'],
        lichess_token=config['lichess_token'],
        chesscom_username=config['chesscom_username'],
        chesscom_password=config['chesscom_password']
    )
    
    scheduler = ELOScheduler(manager, config['config_file'])
    
    if args.action == 'status':
        status = scheduler.get_status()
        print(f"\nScheduler Status:")
        print(f"  Running: {status['running']}")
        print(f"  Configurations: {status['configurations']}")
        print(f"  Enabled: {status['enabled_configurations']}")
        print(f"  Active Tasks: {status['active_tasks']}")
        
        if status['stats']:
            print(f"\nStatistics:")
            for config_name, stats in status['stats'].items():
                print(f"  {config_name}:")
                print(f"    Total Syncs: {stats['total_syncs']}")
                print(f"    Successful: {stats['successful_syncs']}")
                print(f"    Failed: {stats['failed_syncs']}")
                print(f"    Last Sync: {stats['last_sync']}")
                if stats['last_error']:
                    print(f"    Last Error: {stats['last_error']}")
    
    elif args.action == 'start':
        if scheduler.running:
            print("❌ Scheduler is already running")
        else:
            asyncio.create_task(scheduler.start())
            print("✅ Scheduler started")
    
    elif args.action == 'stop':
        scheduler.stop()
        print("✅ Scheduler stopped")
    
    elif args.action == 'add':
        config = SyncConfig(
            bot_names=args.bots,
            platforms=args.platforms,
            interval_minutes=args.interval,
            enabled=not args.disabled
        )
        success = scheduler.add_config(args.name, config)
        if success:
            print(f"✅ Added configuration '{args.name}'")
        else:
            print(f"❌ Failed to add configuration")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="ELO Synchronization CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync ratings from platforms')
    sync_parser.add_argument('platform', choices=['lichess', 'chesscom', 'all'],
                           help='Platform to sync from')
    sync_parser.add_argument('bots', nargs='+', help='Bot names to sync')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List bot ratings')
    list_parser.add_argument('--bot', help='Specific bot name to show')
    
    # Register command
    register_parser = subparsers.add_parser('register', help='Register a new bot')
    register_parser.add_argument('name', help='Bot name')
    register_parser.add_argument('--initial-elo', type=float, default=1500.0,
                               help='Initial ELO rating (default: 1500.0)')
    
    # Mapping command
    mapping_parser = subparsers.add_parser('mapping', help='Manage platform mappings')
    mapping_subparsers = mapping_parser.add_subparsers(dest='action', help='Mapping actions')
    
    set_parser = mapping_subparsers.add_parser('set', help='Set platform mapping')
    set_parser.add_argument('platform', choices=['lichess', 'chesscom'])
    set_parser.add_argument('bot_name', help='Local bot name')
    set_parser.add_argument('platform_username', help='Platform username')
    
    mapping_subparsers.add_parser('list', help='List all mappings')
    
    # Scheduler command
    scheduler_parser = subparsers.add_parser('scheduler', help='Manage scheduler')
    scheduler_subparsers = scheduler_parser.add_subparsers(dest='action', help='Scheduler actions')
    
    scheduler_subparsers.add_parser('status', help='Show scheduler status')
    scheduler_subparsers.add_parser('start', help='Start scheduler')
    scheduler_subparsers.add_parser('stop', help='Stop scheduler')
    
    add_parser = scheduler_subparsers.add_parser('add', help='Add sync configuration')
    add_parser.add_argument('name', help='Configuration name')
    add_parser.add_argument('bots', nargs='+', help='Bot names')
    add_parser.add_argument('--platforms', nargs='+', choices=['lichess', 'chesscom'],
                          default=['lichess', 'chesscom'], help='Platforms to sync')
    add_parser.add_argument('--interval', type=int, default=60,
                          help='Sync interval in minutes (default: 60)')
    add_parser.add_argument('--disabled', action='store_true',
                          help='Create disabled configuration')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Run the appropriate command
    try:
        if args.command == 'sync':
            asyncio.run(cmd_sync(args))
        elif args.command == 'list':
            asyncio.run(cmd_list(args))
        elif args.command == 'register':
            asyncio.run(cmd_register(args))
        elif args.command == 'mapping':
            asyncio.run(cmd_mapping(args))
        elif args.command == 'scheduler':
            asyncio.run(cmd_scheduler(args))
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled")
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()