#!/usr/bin/env python3
"""
Test script to simulate the frontend fix behavior
"""

import requests
import json

def simulate_makeMove():
    """Simulate the makeMove() function behavior"""
    
    print("Simulating makeMove() function...")
    
    # First attempt - should fail with 400
    try:
        response = requests.post('http://127.0.0.1:5000/api/game/move', 
                               json={}, 
                               headers={'Content-Type': 'application/json'})
        
        print(f"First attempt status: {response.status_code}")
        print(f"First attempt response: {response.text}")
        
        if response.status_code == 400:
            print("Move failed because no game is active, starting a new game...")
            
            # Start game (simulating startGame() call)
            start_response = requests.post('http://127.0.0.1:5000/api/game/start', 
                                         json={'white_bot': 'RandomBot', 'black_bot': 'RandomBot'}, 
                                         headers={'Content-Type': 'application/json'})
            
            print(f"Start game status: {start_response.status_code}")
            print(f"Start game response: {start_response.text}")
            
            if start_response.status_code == 200:
                # Try move again after starting game
                print("Trying move again after starting game...")
                move_response = requests.post('http://127.0.0.1:5000/api/game/move', 
                                            json={}, 
                                            headers={'Content-Type': 'application/json'})
                
                print(f"Second move attempt status: {move_response.status_code}")
                print(f"Second move attempt response: {move_response.text}")
            else:
                print("Failed to start game")
        else:
            print("Unexpected response - move succeeded without starting game")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    simulate_makeMove()