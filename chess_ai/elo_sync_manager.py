"""
Central ELO synchronization manager for chess bots.

This module provides a unified interface for synchronizing ELO ratings
across multiple platforms (Lichess, Chess.com) and managing local ratings.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path

from .lichess_api import LichessAPI, LichessELOSync
from .chesscom_api import ChessComAPI, ChessComELOSync

logger = logging.getLogger(__name__)


@dataclass
class BotRating:
    """Represents a bot's rating information."""
    name: str
    elo: float
    games_played: int
    last_updated: datetime
    platform_ratings: Dict[str, Dict[str, Any]]
    confidence: float = 1.0  # 0.0 to 1.0, based on number of games and recency


@dataclass
class SyncResult:
    """Result of a synchronization operation."""
    bot_name: str
    platform: str
    success: bool
    old_elo: float
    new_elo: float
    rating_change: float
    error: Optional[str] = None
    platform_rating: Optional[int] = None
    provisional: bool = False


class ELOPlatform:
    """Enum-like class for supported platforms."""
    LICHESS = "lichess"
    CHESSCOM = "chesscom"
    LOCAL = "local"


class ELOSyncManager:
    """Central manager for ELO synchronization across platforms."""
    
    def __init__(self, 
                 ratings_file: str = "ratings.json",
                 lichess_token: Optional[str] = None,
                 chesscom_username: Optional[str] = None,
                 chesscom_password: Optional[str] = None):
        self.ratings_file = Path(ratings_file)
        self.ratings_data: Dict[str, Any] = {}
        
        # Platform configurations
        self.lichess_token = lichess_token
        self.chesscom_username = chesscom_username
        self.chesscom_password = chesscom_password
        
        # Platform sync instances
        self.lichess_sync: Optional[LichessELOSync] = None
        self.chesscom_sync: Optional[ChessComELOSync] = None
        
        self.load_ratings()
        self._initialize_platforms()
    
    def load_ratings(self):
        """Load ratings data from file."""
        try:
            if self.ratings_file.exists():
                with open(self.ratings_file, 'r') as f:
                    self.ratings_data = json.load(f)
            else:
                self.ratings_data = {
                    "bots": {},
                    "platforms": {
                        "lichess": {"enabled": False, "mapping": {}},
                        "chesscom": {"enabled": False, "mapping": {}}
                    },
                    "sync_history": [],
                    "last_sync": None
                }
                self.save_ratings()
        except Exception as e:
            logger.error(f"Failed to load ratings: {e}")
            self.ratings_data = {"bots": {}, "platforms": {}, "sync_history": []}
    
    def save_ratings(self):
        """Save ratings data to file."""
        try:
            self.ratings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.ratings_file, 'w') as f:
                json.dump(self.ratings_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save ratings: {e}")
    
    def _initialize_platforms(self):
        """Initialize platform sync instances."""
        try:
            if self.lichess_token:
                lichess_api = LichessAPI(self.lichess_token)
                self.lichess_sync = LichessELOSync(lichess_api, str(self.ratings_file))
                self.ratings_data["platforms"]["lichess"]["enabled"] = True
                logger.info("Lichess integration enabled")
        except Exception as e:
            logger.warning(f"Failed to initialize Lichess: {e}")
        
        try:
            if self.chesscom_username:
                chesscom_api = ChessComAPI(self.chesscom_username, self.chesscom_password)
                self.chesscom_sync = ChessComELOSync(chesscom_api, str(self.ratings_file))
                self.ratings_data["platforms"]["chesscom"]["enabled"] = True
                logger.info("Chess.com integration enabled")
        except Exception as e:
            logger.warning(f"Failed to initialize Chess.com: {e}")
    
    def register_bot(self, bot_name: str, initial_elo: float = 1500.0) -> bool:
        """Register a new bot with initial ELO rating."""
        if bot_name in self.ratings_data["bots"]:
            logger.warning(f"Bot {bot_name} already registered")
            return False
        
        self.ratings_data["bots"][bot_name] = {
            "elo": initial_elo,
            "games_played": 0,
            "last_updated": datetime.now().isoformat(),
            "platform_ratings": {},
            "confidence": 1.0
        }
        self.save_ratings()
        logger.info(f"Registered bot {bot_name} with ELO {initial_elo}")
        return True
    
    def get_bot_rating(self, bot_name: str) -> Optional[BotRating]:
        """Get current rating information for a bot."""
        if bot_name not in self.ratings_data["bots"]:
            return None
        
        bot_data = self.ratings_data["bots"][bot_name]
        return BotRating(
            name=bot_name,
            elo=bot_data["elo"],
            games_played=bot_data["games_played"],
            last_updated=datetime.fromisoformat(bot_data["last_updated"]),
            platform_ratings=bot_data.get("platform_ratings", {}),
            confidence=bot_data.get("confidence", 1.0)
        )
    
    def update_bot_rating(self, bot_name: str, new_elo: float, 
                         platform: str = ELOPlatform.LOCAL, 
                         reason: str = "") -> bool:
        """Update a bot's ELO rating."""
        if bot_name not in self.ratings_data["bots"]:
            logger.error(f"Bot {bot_name} not registered")
            return False
        
        old_elo = self.ratings_data["bots"][bot_name]["elo"]
        self.ratings_data["bots"][bot_name].update({
            "elo": new_elo,
            "games_played": self.ratings_data["bots"][bot_name]["games_played"] + 1,
            "last_updated": datetime.now().isoformat(),
            "last_update_reason": reason,
            "last_update_platform": platform
        })
        
        # Update platform-specific rating
        if platform != ELOPlatform.LOCAL:
            if "platform_ratings" not in self.ratings_data["bots"][bot_name]:
                self.ratings_data["bots"][bot_name]["platform_ratings"] = {}
            self.ratings_data["bots"][bot_name]["platform_ratings"][platform] = {
                "rating": new_elo,
                "last_updated": datetime.now().isoformat()
            }
        
        self.save_ratings()
        logger.info(f"Updated {bot_name}: {old_elo:.1f} → {new_elo:.1f} ({platform}, {reason})")
        return True
    
    def set_platform_mapping(self, platform: str, bot_name: str, platform_username: str) -> bool:
        """Set mapping between local bot and platform username."""
        if platform not in self.ratings_data["platforms"]:
            logger.error(f"Platform {platform} not supported")
            return False
        
        if "mapping" not in self.ratings_data["platforms"][platform]:
            self.ratings_data["platforms"][platform]["mapping"] = {}
        
        self.ratings_data["platforms"][platform]["mapping"][bot_name] = platform_username
        self.save_ratings()
        logger.info(f"Set {platform} mapping: {bot_name} → {platform_username}")
        return True
    
    async def sync_platform(self, platform: str, bot_names: List[str]) -> List[SyncResult]:
        """Synchronize ratings from a specific platform."""
        results = []
        
        if platform == ELOPlatform.LICHESS and self.lichess_sync:
            try:
                sync_results = await self.lichess_sync.sync_ratings(bot_names)
                for bot_name, result in sync_results.items():
                    if "error" in result:
                        results.append(SyncResult(
                            bot_name=bot_name,
                            platform=platform,
                            success=False,
                            old_elo=0,
                            new_elo=0,
                            rating_change=0,
                            error=result["error"]
                        ))
                    else:
                        results.append(SyncResult(
                            bot_name=bot_name,
                            platform=platform,
                            success=True,
                            old_elo=result["old_elo"],
                            new_elo=result["new_elo"],
                            rating_change=result["rating_change"],
                            platform_rating=result["lichess_rating"],
                            provisional=result["provisional"]
                        ))
            except Exception as e:
                logger.error(f"Lichess sync failed: {e}")
                for bot_name in bot_names:
                    results.append(SyncResult(
                        bot_name=bot_name,
                        platform=platform,
                        success=False,
                        old_elo=0,
                        new_elo=0,
                        rating_change=0,
                        error=str(e)
                    ))
        
        elif platform == ELOPlatform.CHESSCOM and self.chesscom_sync:
            try:
                sync_results = await self.chesscom_sync.sync_ratings(bot_names)
                for bot_name, result in sync_results.items():
                    if "error" in result:
                        results.append(SyncResult(
                            bot_name=bot_name,
                            platform=platform,
                            success=False,
                            old_elo=0,
                            new_elo=0,
                            rating_change=0,
                            error=result["error"]
                        ))
                    else:
                        results.append(SyncResult(
                            bot_name=bot_name,
                            platform=platform,
                            success=True,
                            old_elo=result["old_elo"],
                            new_elo=result["new_elo"],
                            rating_change=result["rating_change"],
                            platform_rating=result["chesscom_rating"],
                            provisional=result["provisional"]
                        ))
            except Exception as e:
                logger.error(f"Chess.com sync failed: {e}")
                for bot_name in bot_names:
                    results.append(SyncResult(
                        bot_name=bot_name,
                        platform=platform,
                        success=False,
                        old_elo=0,
                        new_elo=0,
                        rating_change=0,
                        error=str(e)
                    ))
        else:
            logger.warning(f"Platform {platform} not available or not configured")
            for bot_name in bot_names:
                results.append(SyncResult(
                    bot_name=bot_name,
                    platform=platform,
                    success=False,
                    old_elo=0,
                    new_elo=0,
                    rating_change=0,
                    error=f"Platform {platform} not configured"
                ))
        
        return results
    
    async def sync_all_platforms(self, bot_names: List[str]) -> Dict[str, List[SyncResult]]:
        """Synchronize ratings from all configured platforms."""
        all_results = {}
        
        # Sync from Lichess
        if self.ratings_data["platforms"]["lichess"]["enabled"]:
            lichess_results = await self.sync_platform(ELOPlatform.LICHESS, bot_names)
            all_results[ELOPlatform.LICHESS] = lichess_results
        
        # Sync from Chess.com
        if self.ratings_data["platforms"]["chesscom"]["enabled"]:
            chesscom_results = await self.sync_platform(ELOPlatform.CHESSCOM, bot_names)
            all_results[ELOPlatform.CHESSCOM] = chesscom_results
        
        # Record sync history
        sync_record = {
            "timestamp": datetime.now().isoformat(),
            "bot_names": bot_names,
            "results": {platform: [asdict(r) for r in results] 
                       for platform, results in all_results.items()}
        }
        self.ratings_data["sync_history"].append(sync_record)
        self.ratings_data["last_sync"] = datetime.now().isoformat()
        
        # Keep only last 100 sync records
        if len(self.ratings_data["sync_history"]) > 100:
            self.ratings_data["sync_history"] = self.ratings_data["sync_history"][-100:]
        
        self.save_ratings()
        return all_results
    
    def get_rating_summary(self) -> Dict[str, Any]:
        """Get summary of all bot ratings."""
        summary = {
            "total_bots": len(self.ratings_data["bots"]),
            "platforms_enabled": {
                platform: data["enabled"] 
                for platform, data in self.ratings_data["platforms"].items()
            },
            "last_sync": self.ratings_data.get("last_sync"),
            "bots": {}
        }
        
        for bot_name, bot_data in self.ratings_data["bots"].items():
            summary["bots"][bot_name] = {
                "elo": bot_data["elo"],
                "games_played": bot_data["games_played"],
                "last_updated": bot_data["last_updated"],
                "confidence": bot_data.get("confidence", 1.0),
                "platform_ratings": bot_data.get("platform_ratings", {})
            }
        
        return summary
    
    def export_ratings(self, format: str = "json") -> str:
        """Export ratings in specified format."""
        if format.lower() == "json":
            return json.dumps(self.get_rating_summary(), indent=2, default=str)
        elif format.lower() == "csv":
            import csv
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Bot", "ELO", "Games", "Last Updated", "Confidence"])
            for bot_name, bot_data in self.ratings_data["bots"].items():
                writer.writerow([
                    bot_name,
                    bot_data["elo"],
                    bot_data["games_played"],
                    bot_data["last_updated"],
                    bot_data.get("confidence", 1.0)
                ])
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")


# Example usage and CLI
async def main():
    """Example usage of the ELO sync manager."""
    # Initialize with platform credentials
    manager = ELOSyncManager(
        lichess_token="your_lichess_token",
        chesscom_username="your_chesscom_username"
    )
    
    # Register bots
    manager.register_bot("DynamicBot", 1500.0)
    manager.register_bot("StockfishBot", 2000.0)
    
    # Set platform mappings
    manager.set_platform_mapping(ELOPlatform.LICHESS, "DynamicBot", "your_lichess_bot")
    manager.set_platform_mapping(ELOPlatform.CHESSCOM, "StockfishBot", "your_chesscom_bot")
    
    # Sync all platforms
    results = await manager.sync_all_platforms(["DynamicBot", "StockfishBot"])
    
    # Print results
    for platform, platform_results in results.items():
        print(f"\n{platform.upper()} Results:")
        for result in platform_results:
            if result.success:
                print(f"  {result.bot_name}: {result.old_elo:.1f} → {result.new_elo:.1f} "
                      f"(+{result.rating_change:.1f})")
            else:
                print(f"  {result.bot_name}: ERROR - {result.error}")
    
    # Export ratings
    print("\nRating Summary:")
    print(manager.export_ratings("json"))


if __name__ == "__main__":
    asyncio.run(main())