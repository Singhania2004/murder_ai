"""WebSocket handlers for real-time game communication."""

from fastapi import WebSocket, WebSocketDisconnect
import json
from app.langgraph.graph import GameGraph
from app.utils.logger import logger
from app.utils.serializers import serialize_game_state, to_json

game_graph = GameGraph()


class ConnectionManager:
    """WebSocket connection manager."""
    
    def __init__(self):
        self.active_connections = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client connected: {client_id}")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client disconnected: {client_id}")
    
    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(to_json(message))
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {str(e)}")


manager = ConnectionManager()


async def handle_websocket(websocket: WebSocket, client_id: str):
    """Handle WebSocket connection."""
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                logger.info(f"Received message from {client_id}: {message.get('action')}")
                
                # Process action
                action = message.get("action")
                
                if action == "start":
                    result = await game_graph.start_game()
                    
                    game_state_data = serialize_game_state(result.get("game_state"))
                    
                    await manager.send_message(client_id, {
                        "type": "game_started",
                        "response": result.get("response"),
                        "game_state": game_state_data
                    })
                
                elif action == "interrogate":
                    # Get current state
                    game_state = game_graph.get_current_state()
                    if not game_state:
                        await manager.send_message(client_id, {
                            "type": "error",
                            "message": "No game in progress. Start a new game first."
                        })
                        continue
                    
                    result = await game_graph.process_action(
                        action="interrogate",
                        user_input=message.get("user_input"),
                        suspect_id=message.get("suspect_id"),
                        evidence=message.get("evidence")
                    )
                    
                    game_state_data = serialize_game_state(result.get("game_state"))
                    
                    await manager.send_message(client_id, {
                        "type": "action_result",
                        "action": action,
                        "response": result.get("response"),  # Raw suspect response
                        "game_state": game_state_data,
                        "game_complete": result.get("game_complete", False),
                        "correct": result.get("correct")
                    })

                elif action == "verify_alibi":
                    game_state = game_graph.get_current_state()
                    if not game_state:
                        await manager.send_message(client_id, {
                            "type": "error",
                            "message": "No game in progress. Start a new game first."
                        })
                        continue
                    
                    result = await game_graph.process_action(
                        action="verify_alibi",
                        suspect_id=message.get("suspect_id")
                    )
                    
                    game_state_data = serialize_game_state(result.get("game_state"))
                    
                    await manager.send_message(client_id, {
                        "type": "action_result",
                        "action": action,
                        "response": result.get("response"),
                        "game_state": game_state_data,
                        "game_complete": result.get("game_complete", False),
                        "correct": result.get("correct")
                    })
                
                elif action == "analyze":
                    game_state = game_graph.get_current_state()
                    if not game_state:
                        await manager.send_message(client_id, {
                            "type": "error",
                            "message": "No game in progress. Start a new game first."
                        })
                        continue
                    
                    result = await game_graph.process_action(
                        action="analyze",
                        clue_id=message.get("clue_id")
                    )
                    
                    game_state_data = serialize_game_state(result.get("game_state"))
                    
                    await manager.send_message(client_id, {
                        "type": "action_result",
                        "action": action,
                        "response": result.get("response"),
                        "game_state": game_state_data,
                        "game_complete": result.get("game_complete", False),
                        "correct": result.get("correct")
                    })
                
                elif action == "discover":
                    game_state = game_graph.get_current_state()
                    if not game_state:
                        await manager.send_message(client_id, {
                            "type": "error",
                            "message": "No game in progress. Start a new game first."
                        })
                        continue
                    
                    result = await game_graph.process_action(
                        action="discover",
                        user_input=message.get("user_input", "the crime scene")
                    )
                    
                    game_state_data = serialize_game_state(result.get("game_state"))
                    
                    await manager.send_message(client_id, {
                        "type": "discover_result",
                        "response": result.get("response"),
                        "game_state": game_state_data,
                        "new_clues": result.get("new_clues", [])
                    })
                
                elif action == "hint":
                    game_state = game_graph.get_current_state()
                    if not game_state:
                        await manager.send_message(client_id, {
                            "type": "error",
                            "message": "No game in progress. Start a new game first."
                        })
                        continue
                    
                    result = await game_graph.process_action(
                        action="hint"
                    )
                    
                    game_state_data = serialize_game_state(result.get("game_state"))
                    
                    await manager.send_message(client_id, {
                        "type": "action_result",
                        "action": action,
                        "response": result.get("response"),
                        "game_state": game_state_data,
                        "game_complete": result.get("game_complete", False),
                        "correct": result.get("correct")
                    })
                
                elif action == "accuse":
                    game_state = game_graph.get_current_state()
                    if not game_state:
                        await manager.send_message(client_id, {
                            "type": "error",
                            "message": "No game in progress. Start a new game first."
                        })
                        continue
                    
                    result = await game_graph.process_action(
                        action="accuse",
                        user_input=message.get("user_input"),
                        motive=message.get("motive")
                    )
                    
                    game_state_data = serialize_game_state(result.get("game_state"))
                    
                    await manager.send_message(client_id, {
                        "type": "action_result",
                        "action": action,
                        "response": result.get("response"),
                        "game_state": game_state_data,
                        "game_complete": result.get("game_complete", False),
                        "correct": result.get("correct")
                    })
                
                elif action == "get_state":
                    game_state = game_graph.get_current_state()
                    game_state_data = serialize_game_state(game_state)
                    await manager.send_message(client_id, {
                        "type": "state",
                        "game_state": game_state_data
                    })
                
                elif action == "reset":
                    game_graph.reset()
                    await manager.send_message(client_id, {
                        "type": "reset",
                        "message": "Game reset"
                    })
                
                else:
                    await manager.send_message(client_id, {
                        "type": "error",
                        "message": f"Unknown action: {action}"
                    })
                    
            except json.JSONDecodeError:
                await manager.send_message(client_id, {
                    "type": "error",
                    "message": "Invalid JSON"
                })
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {str(e)}")
        manager.disconnect(client_id)