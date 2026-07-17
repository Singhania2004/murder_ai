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
        
        killer_status = (
            "You ARE the murderer. Do NOT confess directly — deflect, lie subtly, and project false confidence."
            if suspect.is_killer
            else "You are INNOCENT. React with genuine emotion — confused, irritated, or frightened when accused."
        )
        
        prompt = f"""You are {suspect.name}, the {suspect.role} in a murder investigation being interrogated by a detective.

PERSONALITY: {suspect.personality}
BACKGROUND: {suspect.backstory}
YOUR ALIBI: {suspect.alibi}
YOUR SECRETS: {', '.join(suspect.secrets)}

STATUS: {killer_status}

STRICT OUTPUT RULES — FOLLOW EXACTLY:
- Output ONLY {suspect.name}'s spoken response. Nothing else.
- NO reasoning, NO planning, NO analysis, NO "let me think", NO meta-commentary.
- Start IMMEDIATELY with a physical/emotional expression in [square brackets], then speak.
- Keep it to 2-4 sentences max.
- Use natural speech with contractions (I'm, I've, wasn't, etc.)

FORMAT EXAMPLE:
[crossing arms defensively] I already told the police everything. I was at the charity gala the entire evening — dozens of people saw me there."""
        
        return prompt
    
    async def interrogate(
        self,
        question: str,
        evidence_presented: Optional[List[str]] = None
    ) -> str:
        """Interrogate the suspect with a question."""
        self.interrogation_count += 1
        
        # Build the user message with date/time context
        date_context = f"""
    [Case Date: {self.game_state.case_date or 'Unknown'}]
    [Murder Time: {self.game_state.murder_time or 'Unknown'}]
    """
        
        user_content = f"{date_context}\nDetective: {question}"
        if evidence_presented:
            evidence_str = "\n".join(f"- {e}" for e in evidence_presented)
            user_content = f"{date_context}\n[Evidence shown to you: {evidence_str}]\nDetective: {question}"
        
        # Build messages: system + last 3 prior conversation pairs + current question
        max_history_pairs = 3
        prior_history = self.conversation_history
        recent = prior_history[-(max_history_pairs * 2):]
        
        messages = (
            [{"role": "system", "content": self.system_prompt}]
            + recent
            + [{"role": "user", "content": user_content}]
        )
        
        response = await self._call_chat(
            messages=messages,
            temperature=0.75,
            max_tokens=180
        )
        
        cleaned_response = self._clean_response(response.content)
        
        self.add_to_history("user", user_content)
        self.add_to_history("assistant", cleaned_response)
        self.suspect.statements.append(cleaned_response)
        
        return cleaned_response
    
    def _clean_response(self, response: str) -> str:
        """Remove internal thoughts; preserve [expression] tag at start."""
        # Remove anything between <think> tags (safety net for thinking models)
        cleaned = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        
        # Remove the character's name prefix if it appears (e.g., "James Parker: ")
        cleaned = re.sub(
            r'^' + re.escape(self.suspect.name) + r':\s*',
            '', cleaned, flags=re.IGNORECASE
        ).strip()
        
        # Find the first valid [expression] tag (3–80 chars) and slice from there
        # This strips any leaked reasoning paragraphs before the tag
        match = re.search(r'\[[^\]]{3,80}\]', cleaned)
        if match:
            cleaned = cleaned[match.start():]
        
        # Strip common leaked reasoning patterns that appear before [expression]
        leaked_patterns = [
            r'^Okay[,.]?\s+[^\[][^\n]*\n+',
            r'^Let me think[^\n]*\n+',
            r'^I need to[^\n]*\n+',
            r'^First[,.]?\s+I[^\n]*\n+',
            r'^Wait[,.]?\s[^\n]*\n+',
            r'^Hmm[,.]?\s[^\n]*\n+',
            r'^Alright[,.]?\s[^\n]*\n+',
            r'^So[,.]?\s[^\n]*\n+',
            r'^The detective[^\n]*\n+',
            r'^Since (she|he|I)[^\[^\n]*\n+',
        ]
        
        for pattern in leaked_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
        
        # Collapse multiple blank lines
        cleaned = re.sub(r'\n\s*\n+', '\n\n', cleaned)
        cleaned = cleaned.strip()
        
        # Fallback if we got nothing useful
        if not cleaned or len(cleaned) < 10:
            return "[looking away] I don't have anything to say about that."
        
        # If no expression tag, prepend a neutral one
        if not cleaned.startswith('['):
            cleaned = '[remains guarded] ' + cleaned
        
        return cleaned
    
    async def react_to_accusation(self, accusation: str) -> str:
        """React when accused of the murder."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": (
                    f"Detective: I'm accusing you of the murder! {accusation}\n"
                    f"React with intense emotion. Begin with [expression tag] then speak."
                )
            }
        ]
        
        response = await self._call_chat(
            messages=messages,
            temperature=0.8,
            max_tokens=180
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