"""LangGraph state definitions for the murder mystery game."""

from typing import List, Dict, Any, Optional, Literal, TypedDict
from app.models.state import GameState, Suspect, Clue


class AgentState(TypedDict):
    """State passed between LangGraph nodes."""
    
    # Game state
    game_state: GameState
    
    # Current action
    current_action: str
    current_agent: str
    
    # Input data
    user_input: Optional[str]
    suspect_id: Optional[str]
    clue_id: Optional[str]
    evidence_presented: Optional[List[str]]
    
    # Output data
    response: Optional[str]
    error: Optional[str]
    
    # Control flow
    next_node: str
    iteration: int
    max_iterations: int
    
    # Results
    game_complete: bool
    player_correct: Optional[bool]