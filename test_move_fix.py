#!/usr/bin/env python3
"""
Test script to verify the move fix works correctly
"""

import requests
import json
import time

def test_move_endpoint():
    """Test the move endpoint with different scenarios"""
    
    # Test 1: Try to make a move without starting a game (should get 400)
    print("Test 1: Making move without starting game...")
    try:
        response = requests.post('http://127.0.0.1:5000/api/game/move', 
                               json={}, 
                               headers={'Content-Type': 'application/json'})
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Start a game first, then make a move
    print("Test 2: Starting game then making move...")
    try:
        # Start game
        start_response = requests.post('http://127.0.0.1:5000/api/game/start', 
                                     json={'white_bot': 'RandomBot', 'black_bot': 'RandomBot'}, 
                                     headers={'Content-Type': 'application/json'})
        print(f"Start game status: {start_response.status_code}")
        print(f"Start game response: {start_response.text}")
        
        if start_response.status_code == 200:
            # Make move
            move_response = requests.post('http://127.0.0.1:5000/api/game/move', 
                                        json={}, 
                                        headers={'Content-Type': 'application/json'})
            print(f"Move status: {move_response.status_code}")
            print(f"Move response: {move_response.text}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_move_endpoint()