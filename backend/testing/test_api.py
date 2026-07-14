"""Test the API endpoints."""

import asyncio
import websockets
import json
import requests


def test_rest_api():
    """Test REST API endpoints."""
    base_url = "http://localhost:8000/api"
    
    # Health check
    response = requests.get(f"{base_url}/health")
    print(f"Health: {response.json()}")
    
    # Start game
    response = requests.post(f"{base_url}/game/start")
    print(f"Start game: {response.json().get('response', '')[:200]}...")
    
    game_state = response.json().get("game_state")
    if game_state:
        print(f"Game ID: {game_state.get('game_id')}")
        print(f"Suspects: {len(game_state.get('suspects', []))}")
        
        # Get first suspect
        suspect = game_state["suspects"][0]
        
        # Interrogate
        response = requests.post(
            f"{base_url}/game/action",
            params={
                "action": "interrogate",
                "suspect_id": suspect["id"],
                "user_input": "Where were you at the time of the murder?"
            }
        )
        print(f"Interrogate: {response.json().get('response', '')[:200]}...")


async def test_websocket():
    """Test WebSocket connection."""
    uri = "ws://localhost:8000/ws/test_client"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket")
            
            # Start game
            await websocket.send(json.dumps({"action": "start"}))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Start game response: {data.get('response', '')[:200]}...")
            
            # Get state
            await websocket.send(json.dumps({"action": "get_state"}))
            response = await websocket.recv()
            data = json.loads(response)
            game_state = data.get("game_state")
            
            if game_state:
                suspect = game_state["suspects"][0]
                
                # Interrogate
                await websocket.send(json.dumps({
                    "action": "interrogate",
                    "suspect_id": suspect["id"],
                    "user_input": "What were you doing that night?"
                }))
                response = await websocket.recv()
                data = json.loads(response)
                print(f"Interrogate response: {data.get('response', '')[:200]}...")
            
            print("WebSocket test complete!")
            
    except Exception as e:
        print(f"WebSocket error: {str(e)}")


if __name__ == "__main__":
    print("Testing REST API...")
    test_rest_api()
    
    print("\nTesting WebSocket...")
    asyncio.run(test_websocket())