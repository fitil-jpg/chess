"""
Lichess API integration for ELO rating synchronization.

This module provides functionality to:
- Fetch user ratings from Lichess
- Play games against Lichess bots
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
class LichessUser:
    """Represents a Lichess user with their ratings."""
    username: str
    rating: int
    rating_deviation: int
    provisional: bool
    last_online: Optional[datetime] = None


@dataclass
class LichessGame:
    """Represents a Lichess game."""
    id: str
    white: LichessUser
    black: LichessUser
    result: str  # "1-0", "0-1", "1/2-1/2"
    time_control: str
    rated: bool
    variant: str
    speed: str
    created_at: datetime


class LichessAPI:
    """Client for Lichess API operations."""
    
    BASE_URL = "https://lichess.org/api"
    
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.session: Optional[aiohttp.ClientSession] = None
        self._rate_limit_delay = 0.1  # 100ms between requests
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.token}"} if self.token else {}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a rate-limited request to Lichess API."""
        if not self.session:
            raise RuntimeError("API client not initialized. Use async context manager.")
            
        url = f"{self.BASE_URL}/{endpoint}"
        
        # Rate limiting
        await asyncio.sleep(self._rate_limit_delay)
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 429:
                    # Rate limited, wait longer
                    await asyncio.sleep(1.0)
                    return await self._make_request(endpoint, params)
                    
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Lichess API request failed: {e}")
            raise
    
    async def get_user_rating(self, username: str) -> Optional[LichessUser]:
        """Get current rating for a Lichess user."""
        try:
            data = await self._make_request(f"user/{username}")
            
            # Extract classical rating (or rapid if classical not available)
            rating_data = data.get("perfs", {}).get("classical", {})
            if not rating_data:
                rating_data = data.get("perfs", {}).get("rapid", {})
            
            if not rating_data:
                logger.warning(f"No rating data found for {username}")
                return None
                
            return LichessUser(
                username=username,
                rating=rating_data.get("rating", 1500),
                rating_deviation=rating_data.get("rd", 350),
                provisional=rating_data.get("prog", 0) > 0,
                last_online=datetime.fromtimestamp(data.get("seenAt", 0) / 1000) if data.get("seenAt") else None
            )
        except Exception as e:
            logger.error(f"Failed to get rating for {username}: {e}")
            return None
    
    async def get_bot_ratings(self, bot_usernames: List[str]) -> Dict[str, LichessUser]:
        """Get ratings for multiple bot usernames."""
        ratings = {}
        
        # Process in batches to avoid overwhelming the API
        batch_size = 5
        for i in range(0, len(bot_usernames), batch_size):
            batch = bot_usernames[i:i + batch_size]
            tasks = [self.get_user_rating(username) for username in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for username, result in zip(batch, results):
                if isinstance(result, LichessUser):
                    ratings[username] = result
                elif isinstance(result, Exception):
                    logger.error(f"Error fetching rating for {username}: {result}")
        
        return ratings
    
    async def get_recent_games(self, username: str, max_games: int = 10) -> List[LichessGame]:
        """Get recent games for a user."""
        try:
            params = {
                "max": max_games,
                "rated": "true",
                "perfType": "classical,rapid,blitz"
            }
            data = await self._make_request(f"user/{username}/games", params)
            
            games = []
            for game_data in data:
                try:
                    white_data = game_data.get("players", {}).get("white", {})
                    black_data = game_data.get("players", {}).get("black", {})
                    
                    white_user = LichessUser(
                        username=white_data.get("user", {}).get("name", "Unknown"),
                        rating=white_data.get("rating", 1500),
                        rating_deviation=white_data.get("ratingDiff", 0),
                        provisional=False
                    )
                    
                    black_user = LichessUser(
                        username=black_data.get("user", {}).get("name", "Unknown"),
                        rating=black_data.get("rating", 1500),
                        rating_deviation=black_data.get("ratingDiff", 0),
                        provisional=False
                    )
                    
                    game = LichessGame(
                        id=game_data.get("id", ""),
                        white=white_user,
                        black=black_user,
                        result=game_data.get("winner", "1/2-1/2"),
                        time_control=game_data.get("clock", {}).get("initial", "0"),
                        rated=game_data.get("rated", False),
                        variant=game_data.get("variant", "standard"),
                        speed=game_data.get("speed", "classical"),
                        created_at=datetime.fromtimestamp(game_data.get("createdAt", 0) / 1000)
                    )
                    games.append(game)
                except Exception as e:
                    logger.warning(f"Failed to parse game data: {e}")
                    continue
            
            return games
        except Exception as e:
            logger.error(f"Failed to get recent games for {username}: {e}")
            return []
    
    async def challenge_bot(self, bot_username: str, time_control: str = "300+0", 
                          color: str = "random") -> Optional[str]:
        """Challenge a Lichess bot to a game."""
        if not self.token:
            logger.error("Bot challenging requires authentication token")
            return None
            
        try:
            challenge_data = {
                "username": bot_username,
                "timeControl": time_control,
                "color": color,
                "rated": True
            }
            
            # This would require the Lichess API for challenging bots
            # For now, we'll return a placeholder
            logger.info(f"Would challenge {bot_username} with {time_control}")
            return f"challenge_{bot_username}_{int(time.time())}"
        except Exception as e:
            logger.error(f"Failed to challenge bot {bot_username}: {e}")
            return None


class LichessELOSync:
    """Synchronizes local ELO ratings with Lichess ratings."""
    
    def __init__(self, lichess_api: LichessAPI, local_ratings_file: str = "ratings.json"):
        self.api = lichess_api
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
    
    def get_bot_lichess_mapping(self) -> Dict[str, str]:
        """Get mapping of local bot names to Lichess usernames."""
        return self.local_ratings.get("lichess_mapping", {})
    
    def set_bot_lichess_mapping(self, mapping: Dict[str, str]):
        """Set mapping of local bot names to Lichess usernames."""
        if "lichess_mapping" not in self.local_ratings:
            self.local_ratings["lichess_mapping"] = {}
        self.local_ratings["lichess_mapping"].update(mapping)
        self.save_local_ratings()
    
    async def sync_ratings(self, bot_names: List[str]) -> Dict[str, Dict[str, Any]]:
        """Synchronize ELO ratings for given bot names."""
        mapping = self.get_bot_lichess_mapping()
        lichess_usernames = [mapping.get(bot, bot) for bot in bot_names]
        
        # Get current Lichess ratings
        lichess_ratings = await self.api.get_bot_ratings(lichess_usernames)
        
        sync_results = {}
        
        for bot_name, lichess_username in zip(bot_names, lichess_usernames):
            if lichess_username in lichess_ratings:
                lichess_user = lichess_ratings[lichess_username]
                
                # Update local rating
                if bot_name not in self.local_ratings:
                    self.local_ratings[bot_name] = {
                        "elo": 1500.0,
                        "games_played": 0,
                        "last_updated": datetime.now().isoformat(),
                        "lichess_username": lichess_username
                    }
                
                old_elo = self.local_ratings[bot_name]["elo"]
                new_elo = float(lichess_user.rating)
                
                self.local_ratings[bot_name].update({
                    "elo": new_elo,
                    "lichess_rating": lichess_user.rating,
                    "lichess_rd": lichess_user.rating_deviation,
                    "provisional": lichess_user.provisional,
                    "last_updated": datetime.now().isoformat()
                })
                
                sync_results[bot_name] = {
                    "old_elo": old_elo,
                    "new_elo": new_elo,
                    "lichess_rating": lichess_user.rating,
                    "rating_change": new_elo - old_elo,
                    "provisional": lichess_user.provisional
                }
                
                logger.info(f"Synced {bot_name}: {old_elo:.1f} → {new_elo:.1f} "
                          f"(Lichess: {lichess_user.rating})")
            else:
                logger.warning(f"No Lichess rating found for {bot_name} ({lichess_username})")
                sync_results[bot_name] = {
                    "error": f"No Lichess rating found for {lichess_username}"
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
    """Example of using the Lichess API for ELO synchronization."""
    # You would need to get a Lichess API token from https://lichess.org/account/oauth/token
    token = "your_lichess_token_here"
    
    async with LichessAPI(token) as api:
        sync = LichessELOSync(api)
        
        # Set up bot mappings
        bot_mapping = {
            "DynamicBot": "your_lichess_bot_username",
            "StockfishBot": "your_stockfish_bot_username"
        }
        sync.set_bot_lichess_mapping(bot_mapping)
        
        # Sync ratings
        results = await sync.sync_ratings(["DynamicBot", "StockfishBot"])
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())