"""LangGraph graph definition with proper state management."""

from typing import Dict, Any, Optional, List
from langgraph.graph import StateGraph, END
from app.langgraph.state import AgentState
from app.langgraph.nodes import NodeHandler
from app.utils.logger import logger


class GameGraph:
    """LangGraph game flow definition."""
    
    def __init__(self):
        self.node_handler = NodeHandler()
        self._current_game_state = None
        self._game_initialized = False
        self.graph = self._build_graph()
        self.agent = self.graph.compile()
    
    def _build_graph(self) -> StateGraph:
        """Build the game flow graph."""
        
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("generate_case", self._wrap(self.node_handler.generate_case_node))
        workflow.add_node("interrogate_suspect", self._wrap(self.node_handler.interrogate_suspect_node))
        workflow.add_node("analyze_evidence", self._wrap(self.node_handler.analyze_evidence_node))
        workflow.add_node("discover_evidence", self._wrap(self.node_handler.discover_evidence_node))
        workflow.add_node("get_hint", self._wrap(self.node_handler.get_hint_node))
        workflow.add_node("make_accusation", self._wrap(self.node_handler.make_accusation_node))
        workflow.add_node("end_game", self._wrap(self.node_handler.end_game_node))
        
        # Set entry point
        workflow.set_entry_point("generate_case")
        
        # Conditional edges
        workflow.add_conditional_edges(
            "generate_case",
            self._route_from_generate,
            {
                "awaiting_input": END,
                "error": END
            }
        )
        
        workflow.add_conditional_edges(
            "interrogate_suspect",
            self._route_from_action,
            {
                "awaiting_input": END,
                "error": END
            }
        )
        
        workflow.add_conditional_edges(
            "analyze_evidence",
            self._route_from_action,
            {
                "awaiting_input": END,
                "error": END
            }
        )
        
        workflow.add_conditional_edges(
            "discover_evidence",
            self._route_from_action,
            {
                "awaiting_input": END,
                "error": END
            }
        )
        
        workflow.add_conditional_edges(
            "get_hint",
            self._route_from_action,
            {
                "awaiting_input": END,
                "error": END
            }
        )
        
        workflow.add_conditional_edges(
            "make_accusation",
            self._route_from_accusation,
            {
                "end": "end_game",
                "awaiting_input": END,
                "error": END
            }
        )
        
        workflow.add_edge("end_game", END)
        
        return workflow
    
    def _wrap(self, func):
        """Wrap async function for LangGraph."""
        async def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
            try:
                result = await func(state)
                if result and result.get("game_state"):
                    self._current_game_state = result["game_state"]
                return result
            except Exception as e:
                logger.error(f"Node error: {str(e)}")
                return {
                    "error": str(e),
                    "next_node": "error"
                }
        return wrapper
    
    def _route_from_generate(self, state: Dict[str, Any]) -> str:
        if state.get("error"):
            return "error"
        self._game_initialized = True
        return "awaiting_input"
    
    def _route_from_action(self, state: Dict[str, Any]) -> str:
        if state.get("error"):
            return "error"
        return "awaiting_input"
    
    def _route_from_accusation(self, state: Dict[str, Any]) -> str:
        if state.get("error"):
            return "error"
        if state.get("game_complete"):
            return "end"
        return "awaiting_input"
    
    async def start_game(self) -> Dict[str, Any]:
        """Start a new game."""
        self._game_initialized = False
        self._current_game_state = None
        self.node_handler.suspect_agents.clear()
        
        initial_state = {
            "game_state": None,
            "current_action": "start",
            "current_agent": "generate_case",
            "user_input": None,
            "suspect_id": None,
            "clue_id": None,
            "evidence_presented": None,
            "response": None,
            "error": None,
            "next_node": None,
            "iteration": 0,
            "max_iterations": 10,
            "game_complete": False,
            "player_correct": None
        }
        
        try:
            result = await self.agent.ainvoke(initial_state)
            
            if result and result.get("game_state"):
                self._current_game_state = result["game_state"]
                self._game_initialized = True
            
            response = result.get("response") if result else None
            if not response and result and result.get("error"):
                response = f"Error: {result['error']}"
            elif not response:
                response = "Welcome to the mystery! A case has been generated."
            
            return {
                "response": response,
                "game_state": self._current_game_state,
                "game_complete": result.get("game_complete", False) if result else False,
                "correct": result.get("player_correct") if result else None,
                "error": result.get("error") if result else None
            }
            
        except Exception as e:
            logger.error(f"Graph execution error: {str(e)}")
            return {
                "error": str(e),
                "response": f"Something went wrong: {str(e)}"
            }
    
    async def process_action(
        self,
        action: str,
        game_state: Optional[Any] = None,
        user_input: Optional[str] = None,
        suspect_id: Optional[str] = None,
        clue_id: Optional[str] = None,
        evidence: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Process a player action."""
        
        # Use stored state if no game_state provided
        if game_state is None:
            if self._current_game_state is None:
                return {
                    "error": "No game in progress",
                    "response": "Please start a new game first.",
                    "game_state": None
                }
            game_state = self._current_game_state
        
        # Check if game is complete
        if game_state.solved or game_state.phase == "VERDICT":
            return {
                "error": "Game already complete",
                "response": "The game is over. Start a new game.",
                "game_complete": True,
                "game_state": game_state
            }
        
        # Map action to node
        action_map = {
            "interrogate": "interrogate_suspect",
            "analyze": "analyze_evidence",
            "discover": "discover_evidence",
            "hint": "get_hint",
            "accuse": "make_accusation",
            "verify_alibi": "verify_alibi"  # Add this
        }
        
        node = action_map.get(action)
        if not node:
            return {
                "error": f"Unknown action: {action}",
                "response": "Try: interrogate, discover, analyze, hint, or accuse",
                "game_state": game_state
            }
        
        # Prepare state
        initial_state = {
            "game_state": game_state,
            "current_action": action,
            "current_agent": node,
            "user_input": user_input,
            "suspect_id": suspect_id,
            "clue_id": clue_id,
            "evidence_presented": evidence,
            "response": None,
            "error": None,
            "next_node": None,
            "iteration": 0,
            "max_iterations": 10,
            "game_complete": False,
            "player_correct": None,
            **kwargs
        }
        
        try:
            # Directly call the appropriate node handler
            if node == "interrogate_suspect":
                result = await self.node_handler.interrogate_suspect_node(initial_state)
            # In the node handling section, add:
            elif node == "verify_alibi":
                result = await self.node_handler.verify_alibi_node(initial_state)
            elif node == "analyze_evidence":
                result = await self.node_handler.analyze_evidence_node(initial_state)
            elif node == "discover_evidence":
                result = await self.node_handler.discover_evidence_node(initial_state)
            elif node == "get_hint":
                result = await self.node_handler.get_hint_node(initial_state)
            elif node == "make_accusation":
                result = await self.node_handler.make_accusation_node(initial_state)
            else:
                result = {"error": f"Unknown node: {node}"}
            
            # Store updated state
            if result and result.get("game_state"):
                self._current_game_state = result["game_state"]
                game_state = result["game_state"]
            
            response = result.get("response") if result else None
            if not response and result and result.get("error"):
                response = f"Error: {result['error']}"
            
            return {
                "response": response,
                "game_state": self._current_game_state or game_state,
                "game_complete": result.get("game_complete", False) if result else False,
                "correct": result.get("player_correct") if result else None,
                "error": result.get("error") if result else None,
                "new_clues": result.get("new_clues") if result else None  # For discover action
            }
            
        except Exception as e:
            logger.error(f"Action error: {str(e)}")
            return {
                "error": str(e),
                "response": f"Something went wrong: {str(e)}",
                "game_state": self._current_game_state or game_state
            }
    
    def get_current_state(self):
        """Get the current game state."""
        return self._current_game_state
    
    def reset(self):
        """Reset the game."""
        self._current_game_state = None
        self._game_initialized = False
        self.node_handler.suspect_agents.clear()
