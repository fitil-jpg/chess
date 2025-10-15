#!/usr/bin/env python3
"""
Test script for ELO synchronization system.

This script tests the basic functionality without requiring external API credentials.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from chess_ai.simple_elo_sync import SimpleELOSync


async def test_basic_functionality():
    """Test basic functionality without external APIs."""
    print("Testing ELO sync system...")
    
    # Initialize without external APIs
    sync_system = SimpleELOSync(ratings_file="test_ratings.json")
    
    # Test 1: Register bots
    print("\n1. Testing bot registration...")
    bot_configs = {
        "TestBot1": 1500.0,
        "TestBot2": 1600.0,
        "TestBot3": 1400.0
    }
    register_results = sync_system.register_bots(bot_configs)
    print("Register results:")
    print(json.dumps(register_results, indent=2))
    
    # Test 2: Set platform mappings
    print("\n2. Testing platform mappings...")
    mappings = {
        "lichess": {
            "TestBot1": "test_lichess_bot1",
            "TestBot2": "test_lichess_bot2"
        },
        "chesscom": {
            "TestBot1": "test_chesscom_bot1",
            "TestBot3": "test_chesscom_bot3"
        }
    }
    mapping_results = sync_system.set_platform_mappings(mappings)
    print("Mapping results:")
    print(json.dumps(mapping_results, indent=2))
    
    # Test 3: Manual rating updates
    print("\n3. Testing manual rating updates...")
    success = sync_system.update_bot_rating("TestBot1", 1550.0, "Test update")
    print(f"Manual update successful: {success}")
    
    # Test 4: Get ratings
    print("\n4. Testing rating retrieval...")
    summary = sync_system.get_ratings_summary()
    print("Ratings summary:")
    print(json.dumps(summary, indent=2))
    
    # Test 5: Get specific bot rating
    print("\n5. Testing specific bot rating...")
    bot_rating = sync_system.get_bot_rating("TestBot1")
    print("TestBot1 rating:")
    print(json.dumps(bot_rating, indent=2))
    
    # Test 6: Export ratings
    print("\n6. Testing export...")
    exported = sync_system.export_ratings("json")
    print("Exported ratings:")
    print(exported)
    
    # Test 7: Scheduler setup (without starting)
    print("\n7. Testing scheduler setup...")
    configs = {
        "test_sync": {
            "bot_names": ["TestBot1", "TestBot2"],
            "platforms": ["lichess"],
            "interval_minutes": 30,
            "enabled": False  # Don't actually start
        }
    }
    scheduler_results = sync_system.setup_scheduler(configs)
    print("Scheduler setup results:")
    print(json.dumps(scheduler_results, indent=2))
    
    # Test 8: Scheduler status
    print("\n8. Testing scheduler status...")
    status = sync_system.get_scheduler_status()
    print("Scheduler status:")
    print(json.dumps(status, indent=2))
    
    print("\n✅ All tests completed successfully!")
    print("\nNote: External API sync was not tested because no credentials were provided.")
    print("To test with real APIs, set LICHESS_TOKEN and CHESSCOM_USERNAME environment variables.")


async def test_with_mock_apis():
    """Test with mock API responses."""
    print("\n" + "="*50)
    print("Testing with mock API responses...")
    
    # This would require mocking the API calls
    # For now, just show what would happen
    print("Mock API test would simulate:")
    print("- Lichess API calls")
    print("- Chess.com API calls")
    print("- Rating synchronization")
    print("- Error handling")
    print("\nTo implement mock testing, you would need to:")
    print("1. Mock the aiohttp responses")
    print("2. Simulate different API scenarios")
    print("3. Test error handling")


def test_cli_commands():
    """Test CLI commands."""
    print("\n" + "="*50)
    print("CLI Commands Test:")
    
    commands = [
        "python scripts/simple_elo_sync.py register TestBot --initial-elo 1500",
        "python scripts/simple_elo_sync.py mapping set lichess TestBot test_bot",
        "python scripts/simple_elo_sync.py list",
        "python scripts/simple_elo_sync.py list --bot TestBot",
        "python scripts/simple_elo_sync.py sync TestBot --platforms lichess",
    ]
    
    print("Available CLI commands:")
    for i, cmd in enumerate(commands, 1):
        print(f"{i}. {cmd}")
    
    print("\nTo test CLI commands, run them manually or use subprocess.")


async def main():
    """Main test function."""
    print("ELO Sync System Test Suite")
    print("="*50)
    
    try:
        await test_basic_functionality()
        await test_with_mock_apis()
        test_cli_commands()
        
        print("\n" + "="*50)
        print("Test suite completed!")
        print("\nNext steps:")
        print("1. Set up API credentials in .env file")
        print("2. Run: python examples/simple_elo_example.py")
        print("3. Test with real external APIs")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())