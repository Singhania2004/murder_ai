"""Game state management."""

from typing import List, Dict, Any, Optional, Literal, Union
from pydantic import BaseModel, field_validator
from datetime import datetime
import uuid


class SuspectFacts(BaseModel):
    """Facts about a suspect derived from clues."""
    facts: Dict[str, Any] = {}  # e.g., {"shoe_size": 10, "shoe_brand": "TerraForce", "jacket_color": "black"}
    known_evidence: List[str] = []  # Clue descriptions the suspect knows about


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
    
    # Alibi verification fields
    alibi_verifiable: bool = False
    alibi_truth: bool = False
    alibi_verification_details: str = ""
    alibi_verification_result: Optional[str] = None
    
    # Facts from clues (populated during game state creation)
    facts: Dict[str, Any] = {}  # e.g., {"shoe_size": 10, "shoe_brand": "TerraForce"}
    known_evidence: List[str] = []  # Clue descriptions the suspect knows about


class Witness(BaseModel):
    """Witness data model."""
    id: str
    name: str
    statement: str
    credibility: float = 0.7
    additional_info: Optional[str] = None
    connected_to: Optional[str] = None
    connection_type: Optional[str] = None


class Clue(BaseModel):
    """Clue data model."""
    id: str
    name: str = ""
    description: str
    type: str = "physical"
    is_red_herring: bool = False
    discovered: bool = False
    analyzed: bool = False
    analysis: Optional[str] = None
    
    # New fact-based fields
    belongs_to: Optional[str] = None  # Suspect ID (e.g., "s1") or None for general evidence
    reveals: Dict[str, Any] = {}  # Facts revealed by this clue, e.g., {"shoe_size": 10, "shoe_brand": "TerraForce"}
    known_by_owner: bool = True  # Does the suspect know about this evidence?
    truth: Optional[str] = None  # Optional explanation of what this clue means
    
    @field_validator('type', mode='before')
    @classmethod
    def validate_type(cls, v):
        valid_types = ['physical', 'testimony', 'timeline', 'document', 'hearsay', 'circumstantial', 'witness']
        if v not in valid_types:
            if v in ['hearsay', 'witness']:
                return 'testimony'
            elif v in ['document', 'letter', 'note']:
                return 'document'
            elif v in ['timeline', 'event', 'time']:
                return 'timeline'
            else:
                return 'physical'
        return v


class GameState(BaseModel):
    """Complete game state."""
    # Identifiers
    game_id: str = str(uuid.uuid4())
    session_id: str = str(uuid.uuid4())
    created_at: datetime = datetime.now()
    
    # Game progress
    phase: Literal["INTRO", "INVESTIGATION", "ACCUSATION", "VERDICT"] = "INTRO"
    turn: int = 0
    time_remaining: int = 900
    is_active: bool = True
    
    # Case data
    case_title: str = ""
    case_description: str = ""
    theme: str = ""
    case_date: str = ""
    murder_time: str = ""
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
        for suspect in self.suspects:
            if suspect.id == suspect_id:
                return suspect
        return None
    
    def get_clue(self, clue_id: str) -> Optional[Clue]:
        for clue in self.discovered_clues:
            if clue.id == clue_id:
                return clue
        return None
    
    def get_suspect_by_name(self, name: str) -> Optional[Suspect]:
        """Get a suspect by name (case-insensitive)."""
        for suspect in self.suspects:
            if suspect.name.lower() == name.lower():
                return suspect
        return None
    
    def add_clue(self, clue: Clue):
        self.discovered_clues.append(clue)
    
    def mark_suspect_interrogated(self, suspect_id: str):
        if suspect_id not in self.interrogated_suspect_ids:
            self.interrogated_suspect_ids.append(suspect_id)
        
        suspect = self.get_suspect(suspect_id)
        if suspect:
            suspect.interrogated = True
    
    def build_suspect_facts(self):
        """Build facts for each suspect from their clues."""
        # Reset facts
        for suspect in self.suspects:
            suspect.facts = {}
            suspect.known_evidence = []
        
        # Collect facts from clues
        for clue in self.discovered_clues:
            if clue.belongs_to and clue.reveals:
                suspect = self.get_suspect(clue.belongs_to)
                if suspect:
                    # Add facts
                    for key, value in clue.reveals.items():
                        suspect.facts[key] = value
                    
                    # Add to known evidence if suspect knows about it
                    if clue.known_by_owner:
                        suspect.known_evidence.append(clue.description)
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameState":
        return cls(**data)