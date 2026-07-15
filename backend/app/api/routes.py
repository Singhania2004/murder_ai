"""API routes for the game."""

from fastapi import APIRouter, HTTPException
from typing import Optional
from app.langgraph.graph import GameGraph
from app.utils.logger import logger
from app.utils.serializers import serialize_game_state

router = APIRouter()
game_graph = GameGraph()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "AI Murder Mystery"}


@router.post("/game/start")
async def start_game():
    """Start a new game."""
    try:
        result = await game_graph.start_game()
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "status": "success",
            "game_id": result["game_state"].game_id if result.get("game_state") else None,
            "response": result["response"],
            "game_state": serialize_game_state(result.get("game_state"))
        }
    except Exception as e:
        logger.error(f"Error starting game: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/game/action")
async def process_action(
    action: str,
    user_input: Optional[str] = None,
    suspect_id: Optional[str] = None,
    clue_id: Optional[str] = None,
    evidence: Optional[list] = None,
    motive: Optional[str] = None
):
    """Process a game action."""
    try:
        # Get current game state
        game_state = game_graph.get_current_state()
        if not game_state:
            raise HTTPException(status_code=400, detail="No game in progress. Start a new game first.")
        
        # Process action
        result = await game_graph.process_action(
            action=action,
            user_input=user_input,
            suspect_id=suspect_id,
            clue_id=clue_id,
            evidence=evidence,
            motive=motive
        )
        
        if result.get("error"):
            return {
                "status": "error",
                "message": result["error"],
                "response": result.get("response", "An error occurred.")
            }
        
        return {
            "status": "success",
            "response": result["response"],
            "game_state": serialize_game_state(result.get("game_state")),
            "game_complete": result.get("game_complete", False),
            "correct": result.get("correct")
        }
    except Exception as e:
        logger.error(f"Error processing action: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/game/state")
async def get_game_state():
    """Get the current game state."""
    game_state = game_graph.get_current_state()
    if not game_state:
        return {"status": "error", "message": "No game in progress"}
    
    return {
        "status": "success",
        "game_state": serialize_game_state(game_state)
    }


@router.post("/game/reset")
async def reset_game():
    """Reset the current game."""
    game_graph.reset()
    return {"status": "success", "message": "Game reset"}