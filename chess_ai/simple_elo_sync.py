"""
Simplified ELO synchronization system without web interface.

This module provides a simple CLI-based ELO synchronization system
that outputs results in JSON format for easy parsing.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from .elo_sync_manager import ELOSyncManager, ELOPlatform
from .elo_scheduler import ELOScheduler, SyncConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleELOSync:
    """Simplified ELO synchronization without web interface."""
    
    def __init__(self, 
                 lichess_token: Optional[str] = None,
                 chesscom_username: Optional[str] = None,
                 chesscom_password: Optional[str] = None,
                 ratings_file: str = "ratings.json"):
        self.manager = ELOSyncManager(
            ratings_file=ratings_file,
            lichess_token=lichess_token,
            chesscom_username=chesscom_username,
            chesscom_password=chesscom_password
        )
        self.scheduler: Optional[ELOScheduler] = None
    
    def register_bots(self, bot_configs: Dict[str, float]) -> Dict[str, Any]:
        """Register multiple bots with their initial ELO ratings."""
        results = {}
        for bot_name, initial_elo in bot_configs.items():
            success = self.manager.register_bot(bot_name, initial_elo)
            results[bot_name] = {
                "success": success,
                "initial_elo": initial_elo,
                "message": "Registered" if success else "Already exists"
            }
        return results
    
    def set_platform_mappings(self, mappings: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
        """Set platform mappings for bots."""
        results = {}
        for platform, bot_mappings in mappings.items():
            platform_enum = ELOPlatform.LICHESS if platform == "lichess" else ELOPlatform.CHESSCOM
            for bot_name, platform_username in bot_mappings.items():
                success = self.manager.set_platform_mapping(platform_enum, bot_name, platform_username)
                results[f"{platform}:{bot_name}"] = {
                    "success": success,
                    "platform_username": platform_username,
                    "message": "Mapping set" if success else "Failed to set mapping"
                }
        return results
    
    async def sync_ratings(self, bot_names: List[str], platforms: List[str] = None) -> Dict[str, Any]:
        """Sync ratings for specified bots from specified platforms."""
        if platforms is None:
            platforms = ["lichess", "chesscom"]
        
        results = {}
        
        for platform in platforms:
            if platform == "lichess":
                platform_results = await self.manager.sync_platform(ELOPlatform.LICHESS, bot_names)
            elif platform == "chesscom":
                platform_results = await self.manager.sync_platform(ELOPlatform.CHESSCOM, bot_names)
            else:
                continue
            
            results[platform] = []
            for result in platform_results:
                results[platform].append({
                    "bot_name": result.bot_name,
                    "success": result.success,
                    "old_elo": result.old_elo,
                    "new_elo": result.new_elo,
                    "rating_change": result.rating_change,
                    "error": result.error,
                    "platform_rating": result.platform_rating,
                    "provisional": result.provisional
                })
        
        return results
    
    def get_ratings_summary(self) -> Dict[str, Any]:
        """Get summary of all bot ratings."""
        return self.manager.get_rating_summary()
    
    def get_bot_rating(self, bot_name: str) -> Optional[Dict[str, Any]]:
        """Get rating for a specific bot."""
        rating = self.manager.get_bot_rating(bot_name)
        if rating is None:
            return None
        
        return {
            "name": rating.name,
            "elo": rating.elo,
            "games_played": rating.games_played,
            "last_updated": rating.last_updated.isoformat(),
            "platform_ratings": rating.platform_ratings,
            "confidence": rating.confidence
        }
    
    def update_bot_rating(self, bot_name: str, new_elo: float, reason: str = "") -> bool:
        """Update a bot's ELO rating manually."""
        return self.manager.update_bot_rating(bot_name, new_elo, ELOPlatform.LOCAL, reason)
    
    def export_ratings(self, format: str = "json") -> str:
        """Export ratings in specified format."""
        return self.manager.export_ratings(format)
    
    def setup_scheduler(self, configs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Setup automated scheduler with configurations."""
        self.scheduler = ELOScheduler(self.manager)
        
        results = {}
        for config_name, config_data in configs.items():
            platforms = [ELOPlatform.LICHESS if p == "lichess" else ELOPlatform.CHESSCOM 
                        for p in config_data.get("platforms", ["lichess"])]
            
            config = SyncConfig(
                bot_names=config_data["bot_names"],
                platforms=platforms,
                interval_minutes=config_data.get("interval_minutes", 60),
                enabled=config_data.get("enabled", True)
            )
            
            success = self.scheduler.add_config(config_name, config)
            results[config_name] = {
                "success": success,
                "config": config_data,
                "message": "Configuration added" if success else "Failed to add configuration"
            }
        
        return results
    
    async def start_scheduler(self) -> bool:
        """Start the automated scheduler."""
        if self.scheduler is None:
            return False
        
        if self.scheduler.running:
            return False
        
        asyncio.create_task(self.scheduler.start())
        return True
    
    def stop_scheduler(self) -> bool:
        """Stop the automated scheduler."""
        if self.scheduler is None:
            return False
        
        self.scheduler.stop()
        return True
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        if self.scheduler is None:
            return {"error": "Scheduler not initialized"}
        
        return self.scheduler.get_status()


# CLI Functions
def print_json(data: Any, pretty: bool = True):
    """Print data as JSON."""
    if pretty:
        print(json.dumps(data, indent=2, default=str))
    else:
        print(json.dumps(data, default=str))


async def cmd_sync(sync_system: SimpleELOSync, args):
    """Sync command."""
    platforms = args.platforms if args.platforms else ["lichess", "chesscom"]
    results = await sync_system.sync_ratings(args.bots, platforms)
    print_json(results)


async def cmd_list(sync_system: SimpleELOSync, args):
    """List command."""
    if args.bot:
        rating = sync_system.get_bot_rating(args.bot)
        if rating:
            print_json(rating)
        else:
            print_json({"error": f"Bot '{args.bot}' not found"})
    else:
        summary = sync_system.get_ratings_summary()
        print_json(summary)


async def cmd_register(sync_system: SimpleELOSync, args):
    """Register command."""
    bot_configs = {args.name: args.initial_elo}
    results = sync_system.register_bots(bot_configs)
    print_json(results)


async def cmd_mapping(sync_system: SimpleELOSync, args):
    """Mapping command."""
    if args.action == "set":
        mappings = {args.platform: {args.bot_name: args.platform_username}}
        results = sync_system.set_platform_mappings(mappings)
        print_json(results)
    elif args.action == "list":
        # This would need to be implemented in the manager
        print_json({"message": "List mappings not implemented yet"})


async def cmd_scheduler(sync_system: SimpleELOSync, args):
    """Scheduler command."""
    if args.action == "status":
        status = sync_system.get_scheduler_status()
        print_json(status)
    elif args.action == "start":
        success = await sync_system.start_scheduler()
        print_json({"success": success, "message": "Scheduler started" if success else "Failed to start"})
    elif args.action == "stop":
        success = sync_system.stop_scheduler()
        print_json({"success": success, "message": "Scheduler stopped" if success else "Failed to stop"})


def main():
    """Main CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple ELO Synchronization CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Global options
    parser.add_argument('--ratings-file', default='ratings.json', help='Ratings file path')
    parser.add_argument('--lichess-token', help='Lichess API token')
    parser.add_argument('--chesscom-username', help='Chess.com username')
    parser.add_argument('--chesscom-password', help='Chess.com password')
    parser.add_argument('--quiet', action='store_true', help='Suppress non-JSON output')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync ratings from platforms')
    sync_parser.add_argument('bots', nargs='+', help='Bot names to sync')
    sync_parser.add_argument('--platforms', nargs='+', choices=['lichess', 'chesscom'],
                           help='Platforms to sync from (default: both)')
    
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
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Suppress logging if quiet mode
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    
    # Initialize sync system
    sync_system = SimpleELOSync(
        lichess_token=args.lichess_token or os.getenv('LICHESS_TOKEN'),
        chesscom_username=args.chesscom_username or os.getenv('CHESSCOM_USERNAME'),
        chesscom_password=args.chesscom_password or os.getenv('CHESSCOM_PASSWORD'),
        ratings_file=args.ratings_file
    )
    
    # Run command
    try:
        if args.command == 'sync':
            asyncio.run(cmd_sync(sync_system, args))
        elif args.command == 'list':
            asyncio.run(cmd_list(sync_system, args))
        elif args.command == 'register':
            asyncio.run(cmd_register(sync_system, args))
        elif args.command == 'mapping':
            asyncio.run(cmd_mapping(sync_system, args))
        elif args.command == 'scheduler':
            asyncio.run(cmd_scheduler(sync_system, args))
    except KeyboardInterrupt:
        if not args.quiet:
            print("\nOperation cancelled")
    except Exception as e:
        print_json({"error": str(e)})
        sys.exit(1)


if __name__ == "__main__":
    main()