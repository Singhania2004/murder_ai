"""Game state management."""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel
from datetime import datetime
import uuid


class Suspect(BaseModel):
    """Suspect data model."""
    id: str
    name: str
    role: str
    personality: str
    backstory: str
    alibi: str
    secrets: List[str]
    is_killer: bool = False
    interrogated: bool = False
    statements: List[str] = []


class Witness(BaseModel):
    """Witness data model."""
    id: str
    name: str
    statement: str
    credibility: float  # 0-1, how reliable the witness is
    additional_info: Optional[str] = None


class Clue(BaseModel):
    """Clue data model."""
    id: str
    description: str
    type: Literal["physical", "testimony", "timeline", "document"]
    is_red_herring: bool = False
    discovered: bool = False
    analyzed: bool = False
    analysis: Optional[str] = None


class GameState(BaseModel):
    """Complete game state."""
    # Identifiers
    game_id: str = str(uuid.uuid4())
    session_id: str = str(uuid.uuid4())
    created_at: datetime = datetime.now()
    
    # Game progress
    phase: Literal["INTRO", "INVESTIGATION", "ACCUSATION", "VERDICT"] = "INTRO"
    turn: int = 0
    time_remaining: int = 900  # 15 minutes
    is_active: bool = True
    
    # Case data
    case_title: str = ""
    case_description: str = ""
    victim: Dict[str, Any] = {}
    
    # Characters
    suspects: List[Suspect] = []
    witnesses: List[Witness] = []
    true_killer_id: Optional[str] = None
    motive: str = ""
    timeline: List[Dict[str, str]] = []
    
    # Player discoveries
    discovered_clues: List[Clue] = []
    interrogated_suspect_ids: List[str] = []
    chat_history: List[Dict[str, str]] = []
    player_notes: str = ""
    
    # Game mechanics
    accusations_made: int = 0
    max_accusations: int = 3
    solved: bool = False
    correct_accusation: bool = False
    
    def get_suspect(self, suspect_id: str) -> Optional[Suspect]:
        """Get a suspect by ID."""
        for suspect in self.suspects:
            if suspect.id == suspect_id:
                return suspect
        return None
    
    def get_clue(self, clue_id: str) -> Optional[Clue]:
        """Get a clue by ID."""
        for clue in self.discovered_clues:
            if clue.id == clue_id:
                return clue
        return None
    
    def add_clue(self, clue: Clue):
        """Add a discovered clue."""
        self.discovered_clues.append(clue)
    
    def mark_suspect_interrogated(self, suspect_id: str):
        """Mark a suspect as interrogated."""
        if suspect_id not in self.interrogated_suspect_ids:
            self.interrogated_suspect_ids.append(suspect_id)
        
        suspect = self.get_suspect(suspect_id)
        if suspect:
            suspect.interrogated = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameState":
        """Create from dictionary."""
        return cls(**data)