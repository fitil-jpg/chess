"""
ELO synchronization scheduler for automated rating updates.

This module provides scheduling functionality for regular ELO synchronization
across multiple platforms with configurable intervals and error handling.
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from pathlib import Path

from .elo_sync_manager import ELOSyncManager, ELOPlatform, SyncResult

logger = logging.getLogger(__name__)


@dataclass
class SyncConfig:
    """Configuration for ELO synchronization."""
    bot_names: List[str]
    platforms: List[str]
    interval_minutes: int = 60  # Sync every hour by default
    max_retries: int = 3
    retry_delay_seconds: int = 30
    enabled: bool = True
    notify_on_error: bool = True
    notify_on_success: bool = False


@dataclass
class SyncStats:
    """Statistics for synchronization operations."""
    total_syncs: int = 0
    successful_syncs: int = 0
    failed_syncs: int = 0
    last_sync: Optional[datetime] = None
    last_error: Optional[str] = None
    average_rating_change: float = 0.0


class ELOScheduler:
    """Scheduler for automated ELO synchronization."""
    
    def __init__(self, 
                 manager: ELOSyncManager,
                 config_file: str = "sync_config.json"):
        self.manager = manager
        self.config_file = Path(config_file)
        self.configs: Dict[str, SyncConfig] = {}
        self.stats: Dict[str, SyncStats] = {}
        self.running = False
        self.tasks: List[asyncio.Task] = []
        self.notification_callbacks: List[Callable[[str, List[SyncResult]], None]] = []
        
        self.load_config()
        self.setup_signal_handlers()
    
    def load_config(self):
        """Load synchronization configurations from file."""
        try:
            if self.config_file.exists():
                import json
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                
                for config_name, config_dict in config_data.get("configs", {}).items():
                    self.configs[config_name] = SyncConfig(**config_dict)
                
                logger.info(f"Loaded {len(self.configs)} sync configurations")
            else:
                # Create default configuration
                self.create_default_config()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.create_default_config()
    
    def create_default_config(self):
        """Create default synchronization configuration."""
        default_config = SyncConfig(
            bot_names=["DynamicBot", "StockfishBot"],
            platforms=[ELOPlatform.LICHESS, ELOPlatform.CHESSCOM],
            interval_minutes=60,
            enabled=True
        )
        self.configs["default"] = default_config
        self.save_config()
        logger.info("Created default sync configuration")
    
    def save_config(self):
        """Save synchronization configurations to file."""
        try:
            config_data = {
                "configs": {
                    name: {
                        "bot_names": config.bot_names,
                        "platforms": config.platforms,
                        "interval_minutes": config.interval_minutes,
                        "max_retries": config.max_retries,
                        "retry_delay_seconds": config.retry_delay_seconds,
                        "enabled": config.enabled,
                        "notify_on_error": config.notify_on_error,
                        "notify_on_success": config.notify_on_success
                    }
                    for name, config in self.configs.items()
                }
            }
            
            import json
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def add_config(self, name: str, config: SyncConfig) -> bool:
        """Add a new synchronization configuration."""
        self.configs[name] = config
        self.save_config()
        logger.info(f"Added sync configuration: {name}")
        return True
    
    def remove_config(self, name: str) -> bool:
        """Remove a synchronization configuration."""
        if name in self.configs:
            del self.configs[name]
            self.save_config()
            logger.info(f"Removed sync configuration: {name}")
            return True
        return False
    
    def add_notification_callback(self, callback: Callable[[str, List[SyncResult]], None]):
        """Add a notification callback for sync events."""
        self.notification_callbacks.append(callback)
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run_sync(self, config_name: str) -> List[SyncResult]:
        """Run synchronization for a specific configuration."""
        if config_name not in self.configs:
            logger.error(f"Configuration {config_name} not found")
            return []
        
        config = self.configs[config_name]
        if not config.enabled:
            logger.debug(f"Configuration {config_name} is disabled")
            return []
        
        logger.info(f"Starting sync for {config_name}: {config.bot_names}")
        
        all_results = []
        retry_count = 0
        
        while retry_count <= config.max_retries:
            try:
                # Sync all platforms
                platform_results = await self.manager.sync_all_platforms(config.bot_names)
                
                # Flatten results
                for platform, results in platform_results.items():
                    all_results.extend(results)
                
                # Update statistics
                if config_name not in self.stats:
                    self.stats[config_name] = SyncStats()
                
                stats = self.stats[config_name]
                stats.total_syncs += 1
                stats.last_sync = datetime.now()
                
                successful_results = [r for r in all_results if r.success]
                failed_results = [r for r in all_results if not r.success]
                
                if failed_results:
                    stats.failed_syncs += 1
                    stats.last_error = failed_results[0].error
                    logger.warning(f"Sync {config_name} had {len(failed_results)} failures")
                else:
                    stats.successful_syncs += 1
                    stats.last_error = None
                    logger.info(f"Sync {config_name} completed successfully")
                
                # Calculate average rating change
                if successful_results:
                    total_change = sum(r.rating_change for r in successful_results)
                    stats.average_rating_change = total_change / len(successful_results)
                
                # Send notifications
                if (config.notify_on_error and failed_results) or \
                   (config.notify_on_success and not failed_results):
                    self._send_notifications(config_name, all_results)
                
                break  # Success, exit retry loop
                
            except Exception as e:
                retry_count += 1
                stats = self.stats.get(config_name, SyncStats())
                stats.failed_syncs += 1
                stats.last_error = str(e)
                
                if retry_count <= config.max_retries:
                    logger.warning(f"Sync {config_name} failed (attempt {retry_count}), retrying in {config.retry_delay_seconds}s: {e}")
                    await asyncio.sleep(config.retry_delay_seconds)
                else:
                    logger.error(f"Sync {config_name} failed after {config.max_retries} retries: {e}")
                    self._send_notifications(config_name, [])
                    break
        
        return all_results
    
    def _send_notifications(self, config_name: str, results: List[SyncResult]):
        """Send notifications to registered callbacks."""
        for callback in self.notification_callbacks:
            try:
                callback(config_name, results)
            except Exception as e:
                logger.error(f"Notification callback failed: {e}")
    
    async def _sync_loop(self, config_name: str):
        """Main synchronization loop for a configuration."""
        config = self.configs[config_name]
        
        while self.running:
            try:
                await self.run_sync(config_name)
                
                # Wait for next sync
                await asyncio.sleep(config.interval_minutes * 60)
            except asyncio.CancelledError:
                logger.info(f"Sync loop for {config_name} cancelled")
                break
            except Exception as e:
                logger.error(f"Sync loop for {config_name} error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def start(self):
        """Start the synchronization scheduler."""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        logger.info("Starting ELO synchronization scheduler")
        
        # Start sync loops for all enabled configurations
        for config_name, config in self.configs.items():
            if config.enabled:
                task = asyncio.create_task(self._sync_loop(config_name))
                self.tasks.append(task)
                logger.info(f"Started sync loop for {config_name} (interval: {config.interval_minutes}min)")
        
        # Wait for all tasks to complete
        try:
            await asyncio.gather(*self.tasks)
        except asyncio.CancelledError:
            logger.info("Scheduler tasks cancelled")
        finally:
            self.running = False
    
    def stop(self):
        """Stop the synchronization scheduler."""
        if not self.running:
            return
        
        logger.info("Stopping ELO synchronization scheduler")
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        self.tasks.clear()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status."""
        return {
            "running": self.running,
            "configurations": len(self.configs),
            "enabled_configurations": sum(1 for c in self.configs.values() if c.enabled),
            "active_tasks": len(self.tasks),
            "stats": {
                name: {
                    "total_syncs": stats.total_syncs,
                    "successful_syncs": stats.successful_syncs,
                    "failed_syncs": stats.failed_syncs,
                    "last_sync": stats.last_sync.isoformat() if stats.last_sync else None,
                    "last_error": stats.last_error,
                    "average_rating_change": stats.average_rating_change
                }
                for name, stats in self.stats.items()
            }
        }
    
    def get_config(self, name: str) -> Optional[SyncConfig]:
        """Get a specific configuration."""
        return self.configs.get(name)
    
    def update_config(self, name: str, **kwargs) -> bool:
        """Update a configuration with new values."""
        if name not in self.configs:
            return False
        
        config = self.configs[name]
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        self.save_config()
        logger.info(f"Updated configuration {name}")
        return True


# Notification callbacks
def console_notification(config_name: str, results: List[SyncResult]):
    """Console notification callback."""
    if not results:
        print(f"❌ Sync failed for {config_name}")
        return
    
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    
    if successful:
        print(f"✅ Sync successful for {config_name}:")
        for result in successful:
            print(f"  {result.bot_name}: {result.old_elo:.1f} → {result.new_elo:.1f} "
                  f"(+{result.rating_change:.1f}) on {result.platform}")
    
    if failed:
        print(f"❌ Sync failures for {config_name}:")
        for result in failed:
            print(f"  {result.bot_name}: {result.error}")


def file_notification(log_file: str = "sync_notifications.log"):
    """File notification callback factory."""
    def callback(config_name: str, results: List[SyncResult]):
        timestamp = datetime.now().isoformat()
        with open(log_file, 'a') as f:
            f.write(f"[{timestamp}] {config_name}: {len(results)} results\n")
            for result in results:
                status = "SUCCESS" if result.success else "FAILED"
                f.write(f"  {result.bot_name} ({result.platform}): {status}\n")
                if not result.success and result.error:
                    f.write(f"    Error: {result.error}\n")
    
    return callback


# Example usage
async def main():
    """Example usage of the ELO scheduler."""
    # Initialize manager and scheduler
    manager = ELOSyncManager(
        lichess_token="your_lichess_token",
        chesscom_username="your_chesscom_username"
    )
    
    scheduler = ELOScheduler(manager)
    
    # Add notification callbacks
    scheduler.add_notification_callback(console_notification)
    scheduler.add_notification_callback(file_notification())
    
    # Add custom configuration
    custom_config = SyncConfig(
        bot_names=["DynamicBot", "StockfishBot"],
        platforms=[ELOPlatform.LICHESS],
        interval_minutes=30,  # Sync every 30 minutes
        enabled=True
    )
    scheduler.add_config("frequent_sync", custom_config)
    
    # Start scheduler
    try:
        await scheduler.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
        scheduler.stop()


if __name__ == "__main__":
    asyncio.run(main())