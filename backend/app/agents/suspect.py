"""Suspect Agent - Handles interrogations with personality."""

import json
import re
from typing import Dict, Any, Optional, List
from app.agents.base import BaseAgent
from app.models.state import Suspect, GameState
from app.utils.logger import logger


class SuspectAgent(BaseAgent):
    """Agent representing a suspect in the murder mystery."""
    
    def __init__(self, suspect: Suspect, game_state: GameState):
        """Initialize a suspect agent."""
        self.suspect = suspect
        self.game_state = game_state
        self.interrogation_count = 0
        
        agent_name = f"Suspect: {suspect.name}"
        
        super().__init__(
            name=agent_name,
            role=f"Suspect - {suspect.role}",
            model_type="suspect"
        )
        
        self.system_prompt = self._build_system_prompt()
        logger.info(f"Initialized suspect: {suspect.name} ({suspect.role})")
    
    def update_context(self, game_state: GameState):
        """Update the agent's context with latest game state."""
        self.game_state = game_state
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for this suspect."""
        suspect = self.suspect
        
        killer_status = "You are the MURDERER! You MUST NOT reveal this directly." if suspect.is_killer else "You are INNOCENT."
        
        prompt = f"""You are {suspect.name}, the {suspect.role} in a murder investigation.

PERSONALITY: {suspect.personality}
BACKGROUND: {suspect.backstory}

{killer_status}

YOUR ALIBI: {suspect.alibi}
YOUR SECRETS: {', '.join(suspect.secrets)}

INSTRUCTIONS:
1. Respond ONLY as the character - NO internal thoughts, NO analysis, NO meta-commentary
2. Speak naturally and in character
3. If you are the KILLER: Lie subtly, deflect blame, hide your secrets
4. If you are INNOCENT: Tell the truth but may hide embarrassing details
5. React to evidence presented against you
6. Use natural dialogue with contractions and emotions

IMPORTANT: Your response should be ONLY what {suspect.name} would say. No thinking aloud, no "let me think" or "okay so" - just speak as the character."""
        
        return prompt
    
    async def interrogate(
        self,
        question: str,
        evidence_presented: Optional[List[str]] = None
    ) -> str:
        """Interrogate the suspect with a question."""
        self.interrogation_count += 1
        
        prompt = self._build_interrogation_prompt(question, evidence_presented)
        self.add_to_history("user", question)
        
        response = await self._call_llm(
            prompt=prompt,
            temperature=0.7,
            max_tokens=300
        )
        
        cleaned_response = self._clean_response(response.content)
        
        self.add_to_history("assistant", cleaned_response)
        self.suspect.statements.append(cleaned_response)
        
        return cleaned_response
    
    def _clean_response(self, response: str) -> str:
        """Remove internal thoughts and meta-commentary from response."""
        # Remove anything between <think> tags
        cleaned = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        
        # Remove the character's name prefix if it appears (e.g., "James Parker: ")
        cleaned = re.sub(r'^' + re.escape(self.suspect.name) + r':\s*', '', cleaned, flags=re.IGNORECASE)
        
        # Remove common internal thought patterns
        patterns = [
            r'Okay, so.*?\n',
            r'Let me think.*?\n',
            r'I need to.*?\n',
            r'First, I.*?\n',
            r'Wait,.*?\n',
            r'Hmm,.*?\n',
            r'Since I.*?\n',
            r'But I.*?\n',
            r'Maybe I.*?\n',
            r'I should.*?\n',
            r'Also,.*?\n',
            r'Alright,.*?\n',
            r'Let me.*?\n',
            r'I want to.*?\n',
            r'I could.*?\n',
            r'If I.*?\n',
        ]
        
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
        
        # Remove multiple newlines
        cleaned = re.sub(r'\n\s*\n+', '\n\n', cleaned)
        
        # Strip whitespace
        cleaned = cleaned.strip()
        
        # If cleaned is empty, return a default response
        if not cleaned or len(cleaned) < 10:
            return "I don't have anything to say about that."
        
        return cleaned
    
    def _build_interrogation_prompt(
        self,
        question: str,
        evidence_presented: Optional[List[str]] = None
    ) -> str:
        """Build the interrogation prompt."""
        case_context = f"""
CASE: {self.game_state.case_title}
VICTIM: {self.game_state.victim.get('name', 'Unknown')}
"""
        
        discovered_info = ""
        if self.game_state.discovered_clues:
            discovered_info = "\nEVIDENCE THAT HAS BEEN DISCOVERED:\n"
            for clue in self.game_state.discovered_clues:
                if clue.discovered:
                    discovered_info += f"- {clue.description}\n"
        
        evidence_context = ""
        if evidence_presented:
            evidence_context = "\nEVIDENCE PRESENTED TO YOU:\n"
            for evidence in evidence_presented:
                evidence_context += f"- {evidence}\n"
        
        recent_history = ""
        if self.conversation_history:
            recent_history = "\nRECENT CONVERSATION:\n"
            for msg in self.conversation_history[-4:]:
                role = "Detective" if msg["role"] == "user" else self.suspect.name
                recent_history += f"{role}: {msg['content']}\n"
        
        prompt = f"""{self.system_prompt}

{case_context}
{discovered_info}
{evidence_context}
{recent_history}

Detective: {question}

{self.suspect.name} (respond ONLY as the character, no internal thoughts):
"""
        
        return prompt
    
    async def react_to_accusation(self, accusation: str) -> str:
        """React when accused of the murder."""
        prompt = f"""
You have been ACCUSED of murder!

Accusation: {accusation}

{self.suspect.name} (respond ONLY as the character):
"""
        
        response = await self._call_llm(
            prompt=prompt,
            temperature=0.7,
            max_tokens=200
        )
        
        return self._clean_response(response.content)
    
    async def process(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process an interrogation request."""
        action = input_data.get("action", "interrogate")
        
        if action == "interrogate":
            question = input_data.get("question", "")
            evidence = input_data.get("evidence", [])
            
            response = await self.interrogate(question, evidence)
            
            return {
                "status": "success",
                "response": response,
                "suspect": self.suspect.name,
                "interrogation_count": self.interrogation_count
            }
        
        elif action == "react_to_accusation":
            accusation = input_data.get("accusation", "")
            response = await self.react_to_accusation(accusation)
            
            return {
                "status": "success",
                "response": response,
                "suspect": self.suspect.name
            }
        
        else:
            return {
                "status": "error",
                "message": f"Unknown action: {action}"
            }