"""Game state manager with persistence."""

import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.game import GameSession
from app.models.state import GameState, Suspect, Witness, Clue
from app.utils.logger import logger


class StateManager:
    """Manages game state with persistence."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self._states = {}  # In-memory cache
    
    def create_game(self, game_state: GameState) -> GameState:
        """Create a new game session."""
        try:
            # Convert state to dict
            state_dict = game_state.to_dict()
            
            # Create database record
            db_session = GameSession(
                game_id=game_state.game_id,
                session_id=game_state.session_id,
                phase=game_state.phase,
                turn=game_state.turn,
                time_remaining=game_state.time_remaining,
                is_active=game_state.is_active,
                case_data=state_dict.get("case_data", {}),
                suspects=[s.model_dump() for s in game_state.suspects],
                witnesses=[w.model_dump() for w in game_state.witnesses],
                discovered_clues=[c.model_dump() for c in game_state.discovered_clues],
                interrogated_suspects=game_state.interrogated_suspect_ids,
                chat_history=game_state.chat_history,
                player_notes=game_state.player_notes,
                solved=game_state.solved,
                accusation_made=game_state.accusations_made > 0,
                correct_accusation=game_state.correct_accusation
            )
            
            self.db.add(db_session)
            self.db.commit()
            
            # Cache in memory
            self._states[game_state.game_id] = game_state
            
            logger.info(f"Created game session: {game_state.game_id}")
            return game_state
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating game: {str(e)}")
            raise
    
    def get_game(self, game_id: str) -> Optional[GameState]:
        """Get game state by ID."""
        # Check cache first
        if game_id in self._states:
            return self._states[game_id]
        
        # Query database
        try:
            db_session = self.db.query(GameSession).filter(
                GameSession.game_id == game_id
            ).first()
            
            if not db_session:
                logger.warning(f"Game session not found: {game_id}")
                return None
            
            # Reconstruct state
            state = GameState(
                game_id=db_session.game_id,
                session_id=db_session.session_id,
                phase=db_session.phase,
                turn=db_session.turn,
                time_remaining=db_session.time_remaining,
                is_active=db_session.is_active,
                case_data=db_session.case_data,
                suspects=[Suspect(**s) for s in db_session.suspects],
                witnesses=[Witness(**w) for w in db_session.witnesses],
                discovered_clues=[Clue(**c) for c in db_session.discovered_clues],
                interrogated_suspect_ids=db_session.interrogated_suspects,
                chat_history=db_session.chat_history,
                player_notes=db_session.player_notes,
                solved=db_session.solved,
                correct_accusation=db_session.correct_accusation
            )
            
            # Cache
            self._states[game_id] = state
            
            return state
            
        except Exception as e:
            logger.error(f"Error getting game: {str(e)}")
            return None
    
    def update_game(self, game_state: GameState) -> GameState:
        """Update game state in database."""
        try:
            db_session = self.db.query(GameSession).filter(
                GameSession.game_id == game_state.game_id
            ).first()
            
            if not db_session:
                raise ValueError(f"Game session not found: {game_state.game_id}")
            
            # Update fields
            db_session.phase = game_state.phase
            db_session.turn = game_state.turn
            db_session.time_remaining = game_state.time_remaining
            db_session.is_active = game_state.is_active
            db_session.suspects = [s.model_dump() for s in game_state.suspects]
            db_session.witnesses = [w.model_dump() for w in game_state.witnesses]
            db_session.discovered_clues = [c.model_dump() for c in game_state.discovered_clues]
            db_session.interrogated_suspects = game_state.interrogated_suspect_ids
            db_session.chat_history = game_state.chat_history
            db_session.player_notes = game_state.player_notes
            db_session.solved = game_state.solved
            db_session.accusation_made = game_state.accusations_made > 0
            db_session.correct_accusation = game_state.correct_accusation
            
            self.db.commit()
            
            # Update cache
            self._states[game_state.game_id] = game_state
            
            logger.info(f"Updated game session: {game_state.game_id}")
            return game_state
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating game: {str(e)}")
            raise
    
    def delete_game(self, game_id: str):
        """Delete a game session."""
        try:
            db_session = self.db.query(GameSession).filter(
                GameSession.game_id == game_id
            ).first()
            
            if db_session:
                self.db.delete(db_session)
                self.db.commit()
                
                # Remove from cache
                if game_id in self._states:
                    del self._states[game_id]
                
                logger.info(f"Deleted game session: {game_id}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting game: {str(e)}")
            raise