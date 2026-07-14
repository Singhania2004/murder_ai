"""Game database models."""

from sqlalchemy import Column, String, Integer, DateTime, JSON, Text, Boolean
from sqlalchemy.sql import func
from app.models.base import Base


class GameSession(Base):
    """Store game session data."""
    
    __tablename__ = "game_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String, unique=True, index=True, nullable=False)
    session_id = Column(String, unique=True, index=True, nullable=False)
    
    # Game state
    phase = Column(String, default="INTRO")  # INTRO, INVESTIGATION, ACCUSATION, VERDICT
    turn = Column(Integer, default=0)
    time_remaining = Column(Integer)
    is_active = Column(Boolean, default=True)
    
    # Game data (serialized JSON)
    case_data = Column(JSON)
    suspects = Column(JSON)
    witnesses = Column(JSON)
    discovered_clues = Column(JSON, default=list)
    interrogated_suspects = Column(JSON, default=list)
    chat_history = Column(JSON, default=list)
    player_notes = Column(Text, default="")
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Results
    solved = Column(Boolean, default=False)
    accusation_made = Column(Boolean, default=False)
    correct_accusation = Column(Boolean, default=False)