"""Forensic Expert Agent - Provides cold, factual forensic analysis only."""

from typing import Dict, Any, Optional, List
from app.agents.base import BaseAgent
from app.models.state import Clue, GameState
from app.utils.logger import logger


class ForensicExpert(BaseAgent):
    """Agent that provides cold, factual forensic analysis — no meta-advice."""
    
    def __init__(self):
        super().__init__(
            name="Forensic Expert",
            role="Evidence Analyst",
            model_type="forensic"
        )
        self.system_prompt = """You are a cold, precise forensic scientist reporting findings from a lab.

STRICT RULES:
1. Focus ONLY on forensic facts relevant to a criminal investigation (e.g. shoe sizes, shoe brands, fabric colors/materials, specific items purchased on receipts, timestamps on digital footage/receipts, fingerprints/chemical stains).
2. Cut out useless filler measurements — do NOT report receipt paper dimensions (width/height), paper weight (gsm/grams), or chemical pulp composition of paper. These are completely irrelevant to solving a murder.
3. Be BRIEF — maximum 4 bullet points.
4. Each bullet gives ONE specific, investigation-relevant fact.
5. Do NOT suggest questions to ask suspects or advise next steps.
6. Do NOT say "ask suspects about X" or "you should investigate Y".

Format ONLY as bullet points starting with •
Do NOT include any section headers or advisory text."""
        
        logger.info("Initialized Forensic Expert agent")
    
    async def analyze_evidence(
        self,
        clue: Clue,
        game_state: GameState
    ) -> Dict[str, Any]:
        """Analyze a piece of evidence — returns cold forensic facts only."""
        
        # Build context with date and time information
        case_context = f"""CASE: {game_state.case_title}
VICTIM: {game_state.victim.get('name', 'Unknown')}
CAUSE OF DEATH: {game_state.victim.get('cause_of_death', getattr(game_state, 'method', 'Unknown'))}
CASE DATE: {game_state.case_date or 'Unknown'}
MURDER TIME: {game_state.murder_time or 'Unknown'}

IMPORTANT: The murder occurred at {game_state.murder_time or 'Unknown'} on {game_state.case_date or 'Unknown'}.
If this evidence contains timestamps (CCTV, emails, receipts, phone logs, access logs, etc.),
ensure they are logically consistent with the murder time.
Do not add timestamps to evidence that would not normally have one."""
        
        prompt = f"""Write a forensic lab report for this evidence item.

EVIDENCE ITEM: {clue.description}
EVIDENCE TYPE: {clue.type}

{case_context}

Report ONLY the relevant forensic facts determined from this evidence:
- If a footprint: size, estimated brand, tread design, and estimated stride.
- If a receipt/document: purchase contents (e.g., gun cleaning kit), store name, date, timestamp, and trace markings (such as grease or finger smudges).
- If a fabric/thread/fiber: color, material type, and tear/wear pattern.
- If digital/CCTV: timestamp, subject's height/build description, and visible clothing items.

DO NOT output irrelevant details like paper size, paper weight, or wood pulp composition.
DO NOT mention suspects or advise next steps. Report facts only.
Keep it to 3-4 bullet points maximum."""
        
        response = await self._call_llm(
            prompt=prompt,
            temperature=0.2,
            max_tokens=200
        )
        
        clue.analyzed = True
        clue.analysis = response.content
        
        return {
            "status": "success",
            "clue_id": clue.id,
            "analysis": response.content,
            "clue": clue
        }
    
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