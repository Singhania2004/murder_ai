"""Forensic Expert Agent - Provides specific, actionable analysis."""

from typing import Dict, Any, Optional, List
from app.agents.base import BaseAgent
from app.models.state import Clue, GameState
from app.utils.logger import logger


class ForensicExpert(BaseAgent):
    """Agent that provides specific forensic analysis with concrete details."""
    
    def __init__(self):
        super().__init__(
            name="Forensic Expert",
            role="Evidence Analyst",
            model_type="forensic"
        )
        self.system_prompt = """You are a forensic expert providing SPECIFIC, ACTIONABLE analysis.

RULES:
1. Give CONCRETE details (size 9 shoe, blue cotton fabric, etc.)
2. Suggest what the detective should ask suspects
3. Be BRIEF - max 4 bullet points
4. Don't repeat the evidence description
5. Include specific measurements or details when possible

Format as bullet points starting with •"""
        
        logger.info("Initialized Forensic Expert agent")
    
    async def analyze_evidence(
        self,
        clue: Clue,
        game_state: GameState
    ) -> Dict[str, Any]:
        """Analyze a piece of evidence with specific details."""
        
        suspects_info = self._get_interrogated_suspects_info(game_state)
        
        # Get context about the case
        case_context = f"""
CASE: {game_state.case_title}
VICTIM: {game_state.victim.get('name', 'Unknown')}
MURDER METHOD: {getattr(game_state, 'method', 'Unknown')}
"""
        
        prompt = f"""Analyze this evidence with SPECIFIC details:

EVIDENCE: {clue.description}
TYPE: {clue.type}

{case_context}

INTERROGATED SUSPECTS:
{suspects_info}

Provide a SPECIFIC forensic analysis:
1. What are the concrete details? (size, material, time, etc.)
2. What questions should the detective ask suspects?
3. What should the detective look for next?

Be SPECIFIC and ACTIONABLE. Use numbers, sizes, materials when possible."""
        
        response = await self._call_llm(
            prompt=prompt,
            temperature=0.3,
            max_tokens=180
        )
        
        clue.analyzed = True
        clue.analysis = response.content
        
        return {
            "status": "success",
            "clue_id": clue.id,
            "analysis": response.content,
            "clue": clue
        }
    
    def _get_interrogated_suspects_info(self, game_state: GameState) -> str:
        """Get formatted information only for interrogated suspects."""
        info = []
        interrogated = [s for s in game_state.suspects if s.interrogated]
        
        if not interrogated:
            return "None interrogated yet"
        
        for suspect in interrogated:
            info.append(f"- {suspect.name}: {suspect.alibi}")
        return '\n'.join(info)
    
    async def process(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        action = input_data.get("action", "analyze")
        
        if action == "analyze":
            clue = input_data.get("clue")
            game_state = input_data.get("game_state")
            
            if not clue or not game_state:
                return {
                    "status": "error",
                    "message": "Missing clue or game_state"
                }
            
            result = await self.analyze_evidence(clue, game_state)
            return result
        
        else:
            return {
                "status": "error",
                "message": f"Unknown action: {action}"
            }