#!/usr/bin/env python3
"""
ELO synchronization service with web interface.

This script provides a web service for managing ELO synchronization
with REST API endpoints and a simple web interface.
"""

import asyncio
import json
import logging
import os
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import aiohttp
from aiohttp import web, web_request
from aiohttp.web import Response

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from chess_ai.elo_sync_manager import ELOSyncManager, ELOPlatform
from chess_ai.elo_scheduler import ELOScheduler, console_notification, file_notification

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/logs/elo_sync.log')
    ]
)
logger = logging.getLogger(__name__)

# Global instances
manager: Optional[ELOSyncManager] = None
scheduler: Optional[ELOScheduler] = None


def load_environment():
    """Load configuration from environment variables."""
    return {
        'lichess_token': os.getenv('LICHESS_TOKEN'),
        'chesscom_username': os.getenv('CHESSCOM_USERNAME'),
        'chesscom_password': os.getenv('CHESSCOM_PASSWORD'),
        'ratings_file': os.getenv('RATINGS_FILE', '/app/data/ratings.json'),
        'config_file': os.getenv('CONFIG_FILE', '/app/data/sync_config.json'),
        'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        'port': int(os.getenv('PORT', '8080')),
        'host': os.getenv('HOST', '0.0.0.0')
    }


async def init_manager(config: Dict[str, Any]):
    """Initialize the ELO sync manager."""
    global manager
    manager = ELOSyncManager(
        ratings_file=config['ratings_file'],
        lichess_token=config['lichess_token'],
        chesscom_username=config['chesscom_username'],
        chesscom_password=config['chesscom_password']
    )
    logger.info("ELO sync manager initialized")


async def init_scheduler(config: Dict[str, Any]):
    """Initialize the ELO scheduler."""
    global scheduler
    if manager is None:
        raise RuntimeError("Manager not initialized")
    
    scheduler = ELOScheduler(manager, config['config_file'])
    
    # Add notification callbacks
    scheduler.add_notification_callback(console_notification)
    scheduler.add_notification_callback(file_notification('/app/logs/sync_notifications.log'))
    
    logger.info("ELO scheduler initialized")


# Web API endpoints
async def health_check(request: web_request.Request) -> Response:
    """Health check endpoint."""
    return Response(text=json.dumps({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "manager_initialized": manager is not None,
        "scheduler_running": scheduler.running if scheduler else False
    }), content_type="application/json")


async def get_ratings(request: web_request.Request) -> Response:
    """Get all bot ratings."""
    if manager is None:
        return Response(text=json.dumps({"error": "Manager not initialized"}), 
                       status=500, content_type="application/json")
    
    summary = manager.get_rating_summary()
    return Response(text=json.dumps(summary, default=str), 
                   content_type="application/json")


async def get_bot_rating(request: web_request.Request) -> Response:
    """Get rating for a specific bot."""
    if manager is None:
        return Response(text=json.dumps({"error": "Manager not initialized"}), 
                       status=500, content_type="application/json")
    
    bot_name = request.match_info['bot_name']
    rating = manager.get_bot_rating(bot_name)
    
    if rating is None:
        return Response(text=json.dumps({"error": f"Bot {bot_name} not found"}), 
                       status=404, content_type="application/json")
    
    return Response(text=json.dumps({
        "name": rating.name,
        "elo": rating.elo,
        "games_played": rating.games_played,
        "last_updated": rating.last_updated.isoformat(),
        "platform_ratings": rating.platform_ratings,
        "confidence": rating.confidence
    }, default=str), content_type="application/json")


async def sync_platform(request: web_request.Request) -> Response:
    """Sync ratings from a specific platform."""
    if manager is None:
        return Response(text=json.dumps({"error": "Manager not initialized"}), 
                       status=500, content_type="application/json")
    
    platform = request.match_info['platform']
    data = await request.json()
    bot_names = data.get('bot_names', [])
    
    if not bot_names:
        return Response(text=json.dumps({"error": "No bot names provided"}), 
                       status=400, content_type="application/json")
    
    try:
        results = await manager.sync_platform(platform, bot_names)
        return Response(text=json.dumps({
            "platform": platform,
            "bot_names": bot_names,
            "results": [
                {
                    "bot_name": r.bot_name,
                    "success": r.success,
                    "old_elo": r.old_elo,
                    "new_elo": r.new_elo,
                    "rating_change": r.rating_change,
                    "error": r.error,
                    "platform_rating": r.platform_rating,
                    "provisional": r.provisional
                }
                for r in results
            ]
        }, default=str), content_type="application/json")
    except Exception as e:
        logger.error(f"Sync platform error: {e}")
        return Response(text=json.dumps({"error": str(e)}), 
                       status=500, content_type="application/json")


async def sync_all_platforms(request: web_request.Request) -> Response:
    """Sync ratings from all platforms."""
    if manager is None:
        return Response(text=json.dumps({"error": "Manager not initialized"}), 
                       status=500, content_type="application/json")
    
    data = await request.json()
    bot_names = data.get('bot_names', [])
    
    if not bot_names:
        return Response(text=json.dumps({"error": "No bot names provided"}), 
                       status=400, content_type="application/json")
    
    try:
        results = await manager.sync_all_platforms(bot_names)
        return Response(text=json.dumps({
            "bot_names": bot_names,
            "results": {
                platform: [
                    {
                        "bot_name": r.bot_name,
                        "success": r.success,
                        "old_elo": r.old_elo,
                        "new_elo": r.new_elo,
                        "rating_change": r.rating_change,
                        "error": r.error,
                        "platform_rating": r.platform_rating,
                        "provisional": r.provisional
                    }
                    for r in platform_results
                ]
                for platform, platform_results in results.items()
            }
        }, default=str), content_type="application/json")
    except Exception as e:
        logger.error(f"Sync all platforms error: {e}")
        return Response(text=json.dumps({"error": str(e)}), 
                       status=500, content_type="application/json")


async def get_scheduler_status(request: web_request.Request) -> Response:
    """Get scheduler status."""
    if scheduler is None:
        return Response(text=json.dumps({"error": "Scheduler not initialized"}), 
                       status=500, content_type="application/json")
    
    status = scheduler.get_status()
    return Response(text=json.dumps(status, default=str), 
                   content_type="application/json")


async def start_scheduler(request: web_request.Request) -> Response:
    """Start the scheduler."""
    if scheduler is None:
        return Response(text=json.dumps({"error": "Scheduler not initialized"}), 
                       status=500, content_type="application/json")
    
    if scheduler.running:
        return Response(text=json.dumps({"message": "Scheduler already running"}), 
                       content_type="application/json")
    
    # Start scheduler in background
    asyncio.create_task(scheduler.start())
    return Response(text=json.dumps({"message": "Scheduler started"}), 
                   content_type="application/json")


async def stop_scheduler(request: web_request.Request) -> Response:
    """Stop the scheduler."""
    if scheduler is None:
        return Response(text=json.dumps({"error": "Scheduler not initialized"}), 
                       status=500, content_type="application/json")
    
    scheduler.stop()
    return Response(text=json.dumps({"message": "Scheduler stopped"}), 
                   content_type="application/json")


async def web_interface(request: web_request.Request) -> Response:
    """Simple web interface."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ELO Sync Service</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; }
            .section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; }
            button { padding: 10px 20px; margin: 5px; cursor: pointer; }
            .status { padding: 10px; margin: 10px 0; border-radius: 4px; }
            .success { background-color: #d4edda; color: #155724; }
            .error { background-color: #f8d7da; color: #721c24; }
            pre { background-color: #f8f9fa; padding: 10px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>ELO Sync Service</h1>
            
            <div class="section">
                <h2>Bot Ratings</h2>
                <button onclick="loadRatings()">Refresh Ratings</button>
                <div id="ratings"></div>
            </div>
            
            <div class="section">
                <h2>Manual Sync</h2>
                <button onclick="syncAll()">Sync All Platforms</button>
                <div id="sync-result"></div>
            </div>
            
            <div class="section">
                <h2>Scheduler Status</h2>
                <button onclick="loadSchedulerStatus()">Refresh Status</button>
                <button onclick="startScheduler()">Start Scheduler</button>
                <button onclick="stopScheduler()">Stop Scheduler</button>
                <div id="scheduler-status"></div>
            </div>
        </div>
        
        <script>
            async function loadRatings() {
                try {
                    const response = await fetch('/api/ratings');
                    const data = await response.json();
                    document.getElementById('ratings').innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                } catch (error) {
                    document.getElementById('ratings').innerHTML = '<div class="status error">Error: ' + error + '</div>';
                }
            }
            
            async function syncAll() {
                try {
                    const response = await fetch('/api/sync/all', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ bot_names: ['DynamicBot', 'StockfishBot'] })
                    });
                    const data = await response.json();
                    document.getElementById('sync-result').innerHTML = '<div class="status success">Sync completed</div><pre>' + JSON.stringify(data, null, 2) + '</pre>';
                } catch (error) {
                    document.getElementById('sync-result').innerHTML = '<div class="status error">Error: ' + error + '</div>';
                }
            }
            
            async function loadSchedulerStatus() {
                try {
                    const response = await fetch('/api/scheduler/status');
                    const data = await response.json();
                    document.getElementById('scheduler-status').innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                } catch (error) {
                    document.getElementById('scheduler-status').innerHTML = '<div class="status error">Error: ' + error + '</div>';
                }
            }
            
            async function startScheduler() {
                try {
                    const response = await fetch('/api/scheduler/start', { method: 'POST' });
                    const data = await response.json();
                    document.getElementById('scheduler-status').innerHTML = '<div class="status success">' + data.message + '</div>';
                } catch (error) {
                    document.getElementById('scheduler-status').innerHTML = '<div class="status error">Error: ' + error + '</div>';
                }
            }
            
            async function stopScheduler() {
                try {
                    const response = await fetch('/api/scheduler/stop', { method: 'POST' });
                    const data = await response.json();
                    document.getElementById('scheduler-status').innerHTML = '<div class="status success">' + data.message + '</div>';
                } catch (error) {
                    document.getElementById('scheduler-status').innerHTML = '<div class="status error">Error: ' + error + '</div>';
                }
            }
            
            // Load initial data
            loadRatings();
            loadSchedulerStatus();
        </script>
    </body>
    </html>
    """
    return Response(text=html, content_type="text/html")


def setup_routes(app: web.Application):
    """Setup web application routes."""
    # Health check
    app.router.add_get('/health', health_check)
    
    # API endpoints
    app.router.add_get('/api/ratings', get_ratings)
    app.router.add_get('/api/ratings/{bot_name}', get_bot_rating)
    app.router.add_post('/api/sync/{platform}', sync_platform)
    app.router.add_post('/api/sync/all', sync_all_platforms)
    app.router.add_get('/api/scheduler/status', get_scheduler_status)
    app.router.add_post('/api/scheduler/start', start_scheduler)
    app.router.add_post('/api/scheduler/stop', stop_scheduler)
    
    # Web interface
    app.router.add_get('/', web_interface)


async def main():
    """Main application entry point."""
    # Load configuration
    config = load_environment()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, config['log_level'].upper()))
    
    logger.info("Starting ELO sync service")
    
    # Initialize components
    await init_manager(config)
    await init_scheduler(config)
    
    # Create web application
    app = web.Application()
    setup_routes(app)
    
    # Setup graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        if scheduler:
            scheduler.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start web server
    logger.info(f"Starting web server on {config['host']}:{config['port']}")
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, config['host'], config['port'])
    await site.start()
    
    # Start scheduler in background
    if scheduler:
        asyncio.create_task(scheduler.start())
        logger.info("Scheduler started")
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        if scheduler:
            scheduler.stop()
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())