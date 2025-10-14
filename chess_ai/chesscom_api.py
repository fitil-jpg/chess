"""
Chess.com API integration for ELO rating synchronization.

This module provides functionality to:
- Fetch user ratings from Chess.com
- Play games against Chess.com bots
- Update local ELO ratings based on external results
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

import aiohttp
import chess
import chess.engine

logger = logging.getLogger(__name__)


@dataclass
class ChessComUser:
    """Represents a Chess.com user with their ratings."""
    username: str
    rating: int
    rating_deviation: int
    provisional: bool
    last_online: Optional[datetime] = None
    country: Optional[str] = None
    title: Optional[str] = None


@dataclass
class ChessComGame:
    """Represents a Chess.com game."""
    id: str
    white: ChessComUser
    black: ChessComUser
    result: str  # "1-0", "0-1", "1/2-1/2"
    time_control: str
    rated: bool
    variant: str
    speed: str
    created_at: datetime
    pgn: Optional[str] = None


class ChessComAPI:
    """Client for Chess.com API operations."""
    
    BASE_URL = "https://api.chess.com"
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        self.username = username
        self.password = password
        self.session: Optional[aiohttp.ClientSession] = None
        self._rate_limit_delay = 0.1  # 100ms between requests
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a rate-limited request to Chess.com API."""
        if not self.session:
            raise RuntimeError("API client not initialized. Use async context manager.")
            
        url = f"{self.BASE_URL}/{endpoint}"
        
        # Rate limiting
        await asyncio.sleep(self._rate_limit_delay)
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 429:
                    # Rate limited, wait longer
                    await asyncio.sleep(2.0)
                    return await self._make_request(endpoint, params)
                    
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Chess.com API request failed: {e}")
            raise
    
    async def get_user_profile(self, username: str) -> Optional[ChessComUser]:
        """Get profile information for a Chess.com user."""
        try:
            data = await self._make_request(f"pub/player/{username}")
            
            # Extract rating information
            stats = data.get("stats", {})
            
            # Try different time controls in order of preference
            rating_data = None
            for time_control in ["chess_rapid", "chess_blitz", "chess_daily", "chess_bullet"]:
                if time_control in stats and "last" in stats[time_control]:
                    rating_data = stats[time_control]["last"]
                    break
            
            if not rating_data:
                logger.warning(f"No rating data found for {username}")
                return None
                
            return ChessComUser(
                username=username,
                rating=rating_data.get("rating", 1500),
                rating_deviation=rating_data.get("rd", 350),
                provisional=rating_data.get("prog", 0) > 0,
                last_online=datetime.fromtimestamp(data.get("last_online", 0)) if data.get("last_online") else None,
                country=data.get("country"),
                title=data.get("title")
            )
        except Exception as e:
            logger.error(f"Failed to get profile for {username}: {e}")
            return None
    
    async def get_user_ratings(self, username: str) -> Dict[str, int]:
        """Get all ratings for a Chess.com user."""
        try:
            data = await self._make_request(f"pub/player/{username}/stats")
            
            ratings = {}
            stats = data.get("stats", {})
            
            for time_control, stats_data in stats.items():
                if "last" in stats_data and "rating" in stats_data["last"]:
                    ratings[time_control] = stats_data["last"]["rating"]
            
            return ratings
        except Exception as e:
            logger.error(f"Failed to get ratings for {username}: {e}")
            return {}
    
    async def get_bot_ratings(self, bot_usernames: List[str]) -> Dict[str, ChessComUser]:
        """Get ratings for multiple bot usernames."""
        ratings = {}
        
        # Process in batches to avoid overwhelming the API
        batch_size = 3  # Chess.com has stricter rate limits
        for i in range(0, len(bot_usernames), batch_size):
            batch = bot_usernames[i:i + batch_size]
            tasks = [self.get_user_profile(username) for username in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for username, result in zip(batch, results):
                if isinstance(result, ChessComUser):
                    ratings[username] = result
                elif isinstance(result, Exception):
                    logger.error(f"Error fetching profile for {username}: {result}")
            
            # Extra delay between batches
            if i + batch_size < len(bot_usernames):
                await asyncio.sleep(1.0)
        
        return ratings
    
    async def get_recent_games(self, username: str, max_games: int = 10) -> List[ChessComGame]:
        """Get recent games for a user."""
        try:
            # Get games from different archives
            games = []
            
            # Get current month's games
            now = datetime.now()
            year = now.year
            month = now.month
            
            for _ in range(3):  # Check last 3 months
                try:
                    data = await self._make_request(f"pub/player/{username}/games/{year}/{month:02d}")
                    
                    for game_data in data.get("games", []):
                        try:
                            white_data = game_data.get("white", {})
                            black_data = game_data.get("black", {})
                            
                            white_user = ChessComUser(
                                username=white_data.get("username", "Unknown"),
                                rating=white_data.get("rating", 1500),
                                rating_deviation=0,  # Chess.com doesn't provide RD
                                provisional=False
                            )
                            
                            black_user = ChessComUser(
                                username=black_data.get("username", "Unknown"),
                                rating=black_data.get("rating", 1500),
                                rating_deviation=0,
                                provisional=False
                            )
                            
                            # Determine result
                            result = "1/2-1/2"
                            if game_data.get("white", {}).get("result") == "win":
                                result = "1-0"
                            elif game_data.get("black", {}).get("result") == "win":
                                result = "0-1"
                            
                            game = ChessComGame(
                                id=str(game_data.get("url", "")),
                                white=white_user,
                                black=black_user,
                                result=result,
                                time_control=str(game_data.get("time_control", "0")),
                                rated=game_data.get("rated", False),
                                variant=game_data.get("rules", "standard"),
                                speed=game_data.get("time_class", "rapid"),
                                created_at=datetime.fromtimestamp(game_data.get("end_time", 0)),
                                pgn=game_data.get("pgn")
                            )
                            games.append(game)
                            
                            if len(games) >= max_games:
                                break
                                
                        except Exception as e:
                            logger.warning(f"Failed to parse game data: {e}")
                            continue
                    
                    if len(games) >= max_games:
                        break
                        
                except Exception as e:
                    logger.warning(f"Failed to get games for {year}/{month:02d}: {e}")
                
                # Move to previous month
                month -= 1
                if month <= 0:
                    month = 12
                    year -= 1
            
            return games[:max_games]
        except Exception as e:
            logger.error(f"Failed to get recent games for {username}: {e}")
            return []
    
    async def get_leaderboard(self, time_control: str = "rapid", limit: int = 50) -> List[ChessComUser]:
        """Get leaderboard for a specific time control."""
        try:
            data = await self._make_request(f"pub/leaderboards/{time_control}")
            
            users = []
            for player_data in data.get("players", [])[:limit]:
                try:
                    user = ChessComUser(
                        username=player_data.get("username", "Unknown"),
                        rating=player_data.get("rating", 1500),
                        rating_deviation=0,
                        provisional=False,
                        country=player_data.get("country"),
                        title=player_data.get("title")
                    )
                    users.append(user)
                except Exception as e:
                    logger.warning(f"Failed to parse leaderboard player: {e}")
                    continue
            
            return users
        except Exception as e:
            logger.error(f"Failed to get leaderboard for {time_control}: {e}")
            return []


class ChessComELOSync:
    """Synchronizes local ELO ratings with Chess.com ratings."""
    
    def __init__(self, chesscom_api: ChessComAPI, local_ratings_file: str = "ratings.json"):
        self.api = chesscom_api
        self.ratings_file = local_ratings_file
        self.local_ratings: Dict[str, Dict[str, Any]] = {}
        self.load_local_ratings()
    
    def load_local_ratings(self):
        """Load local ELO ratings from file."""
        try:
            with open(self.ratings_file, 'r') as f:
                self.local_ratings = json.load(f)
        except FileNotFoundError:
            self.local_ratings = {}
            logger.info(f"Created new ratings file: {self.ratings_file}")
        except Exception as e:
            logger.error(f"Failed to load local ratings: {e}")
            self.local_ratings = {}
    
    def save_local_ratings(self):
        """Save local ELO ratings to file."""
        try:
            with open(self.ratings_file, 'w') as f:
                json.dump(self.local_ratings, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save local ratings: {e}")
    
    def get_bot_chesscom_mapping(self) -> Dict[str, str]:
        """Get mapping of local bot names to Chess.com usernames."""
        return self.local_ratings.get("chesscom_mapping", {})
    
    def set_bot_chesscom_mapping(self, mapping: Dict[str, str]):
        """Set mapping of local bot names to Chess.com usernames."""
        if "chesscom_mapping" not in self.local_ratings:
            self.local_ratings["chesscom_mapping"] = {}
        self.local_ratings["chesscom_mapping"].update(mapping)
        self.save_local_ratings()
    
    async def sync_ratings(self, bot_names: List[str], time_control: str = "rapid") -> Dict[str, Dict[str, Any]]:
        """Synchronize ELO ratings for given bot names."""
        mapping = self.get_bot_chesscom_mapping()
        chesscom_usernames = [mapping.get(bot, bot) for bot in bot_names]
        
        # Get current Chess.com ratings
        chesscom_ratings = await self.api.get_bot_ratings(chesscom_usernames)
        
        sync_results = {}
        
        for bot_name, chesscom_username in zip(bot_names, chesscom_usernames):
            if chesscom_username in chesscom_ratings:
                chesscom_user = chesscom_ratings[chesscom_username]
                
                # Update local rating
                if bot_name not in self.local_ratings:
                    self.local_ratings[bot_name] = {
                        "elo": 1500.0,
                        "games_played": 0,
                        "last_updated": datetime.now().isoformat(),
                        "chesscom_username": chesscom_username
                    }
                
                old_elo = self.local_ratings[bot_name]["elo"]
                new_elo = float(chesscom_user.rating)
                
                self.local_ratings[bot_name].update({
                    "elo": new_elo,
                    "chesscom_rating": chesscom_user.rating,
                    "chesscom_rd": chesscom_user.rating_deviation,
                    "provisional": chesscom_user.provisional,
                    "last_updated": datetime.now().isoformat(),
                    "time_control": time_control
                })
                
                sync_results[bot_name] = {
                    "old_elo": old_elo,
                    "new_elo": new_elo,
                    "chesscom_rating": chesscom_user.rating,
                    "rating_change": new_elo - old_elo,
                    "provisional": chesscom_user.provisional,
                    "time_control": time_control
                }
                
                logger.info(f"Synced {bot_name}: {old_elo:.1f} → {new_elo:.1f} "
                          f"(Chess.com {time_control}: {chesscom_user.rating})")
            else:
                logger.warning(f"No Chess.com rating found for {bot_name} ({chesscom_username})")
                sync_results[bot_name] = {
                    "error": f"No Chess.com rating found for {chesscom_username}"
                }
        
        self.save_local_ratings()
        return sync_results
    
    def get_bot_rating(self, bot_name: str) -> float:
        """Get current ELO rating for a bot."""
        return self.local_ratings.get(bot_name, {}).get("elo", 1500.0)
    
    def update_bot_rating(self, bot_name: str, new_elo: float, reason: str = ""):
        """Update a bot's ELO rating locally."""
        if bot_name not in self.local_ratings:
            self.local_ratings[bot_name] = {
                "elo": 1500.0,
                "games_played": 0,
                "last_updated": datetime.now().isoformat()
            }
        
        old_elo = self.local_ratings[bot_name]["elo"]
        self.local_ratings[bot_name].update({
            "elo": new_elo,
            "games_played": self.local_ratings[bot_name].get("games_played", 0) + 1,
            "last_updated": datetime.now().isoformat(),
            "last_update_reason": reason
        })
        
        logger.info(f"Updated {bot_name}: {old_elo:.1f} → {new_elo:.1f} ({reason})")
        self.save_local_ratings()


# Example usage
async def main():
    """Example of using the Chess.com API for ELO synchronization."""
    async with ChessComAPI() as api:
        sync = ChessComELOSync(api)
        
        # Set up bot mappings
        bot_mapping = {
            "DynamicBot": "your_chesscom_bot_username",
            "StockfishBot": "your_stockfish_bot_username"
        }
        sync.set_bot_chesscom_mapping(bot_mapping)
        
        # Sync ratings
        results = await sync.sync_ratings(["DynamicBot", "StockfishBot"], time_control="rapid")
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())