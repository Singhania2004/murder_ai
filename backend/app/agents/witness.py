"""Witness Agent - Provides testimony about what they saw."""

from typing import Dict, Any, Optional, List
from app.agents.base import BaseAgent
from app.models.state import Witness, GameState
from app.utils.logger import logger


class WitnessAgent(BaseAgent):
    """Agent representing a witness in the case."""
    
    def __init__(self, witness: Witness, game_state: GameState):
        """
        Initialize a witness agent.
        
        Args:
            witness: The witness data
            game_state: Current game state
        """
        self.witness = witness
        self.game_state = game_state
        self.testimony_count = 0
        
        agent_name = f"Witness: {witness.name}"
        
        super().__init__(
            name=agent_name,
            role="Witness",
            model_type="forensic"  # Use factual model
        )
        
        self.system_prompt = self._build_system_prompt()
        logger.info(f"Initialized witness: {witness.name}")
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for this witness."""
        
        prompt = f"""You are {self.witness.name}, a witness in a murder investigation.

WHAT YOU SAW/HEARD:
{self.witness.statement}

YOUR CREDIBILITY: {self.witness.credibility}/1.0
{self.witness.additional_info or ""}

INSTRUCTIONS:
1. Tell the truth about what you saw and heard
2. If you're unsure about something, say so
3. You may have additional details that aren't in your initial statement
4. You're credible - you believe what you're saying is true
5. However, you may have gotten some details wrong (eyewitness error is common)

CONVERSATION STYLE:
- Speak naturally as an ordinary person
- Use casual language
- Be cooperative with the detective
- Show appropriate emotions (fear, excitement, concern, etc.)"""
        
        return prompt
    
    async def testify(
        self,
        question: str,
        evidence_context: Optional[List[str]] = None
    ) -> str:
        """
        Testify in response to a question.
        
        Args:
            question: The question being asked
            evidence_context: Other evidence being presented
        
        Returns:
            The witness's testimony
        """
        self.testimony_count += 1
        
        # Build prompt with context
        prompt = self._build_testimony_prompt(question, evidence_context)
        
        # Get response
        response = await self._call_llm(
            prompt=prompt,
            temperature=0.6,  # Moderate temperature for testimony
            max_tokens=512
        )
        
        self.add_to_history("user", question)
        self.add_to_history("assistant", response.content)
        
        return response.content
    
    def _build_testimony_prompt(
        self,
        question: str,
        evidence_context: Optional[List[str]] = None
    ) -> str:
        """Build the testimony prompt."""
        
        # Context about the case
        context = f"""
CASE: {self.game_state.case_title}
VICTIM: {self.game_state.victim.get('name', 'Unknown')}
"""
        
        # Evidence context
        evidence_text = ""
        if evidence_context:
            evidence_text = "\nOTHER EVIDENCE MENTIONED:\n"
            for evidence in evidence_context:
                evidence_text += f"- {evidence}\n"
        
        # Previous statements (if any)
        history_text = ""
        if self.conversation_history:
            history_text = "\nPREVIOUS TESTIMONY:\n"
            for msg in self.conversation_history[-4:]:
                role = "Detective" if msg["role"] == "user" else self.witness.name
                history_text += f"{role}: {msg['content']}\n"
        
        prompt = f"""{self.system_prompt}

{context}
{evidence_text}
{history_text}

Detective Question: {question}

{self.witness.name}'s testimony:
"""
        
        return prompt
    
    async def process(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a testimony request."""
        
        action = input_data.get("action", "testify")
        
        if action == "testify":
            question = input_data.get("question", "")
            evidence = input_data.get("evidence", [])
            
            response = await self.testify(question, evidence)
            
            return {
                "status": "success",
                "response": response,
                "witness": self.witness.name,
                "credibility": self.witness.credibility
            }
        
        else:
            return {
                "status": "error",
                "message": f"Unknown action: {action}"
            }