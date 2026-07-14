"""Crime Scene Generator Agent - Creates murder cases dynamically."""

import json
import uuid
import re
import random
from typing import Dict, Any, List, Optional
from app.agents.base import BaseAgent
from app.models.state import Suspect, Witness, Clue, GameState
from app.utils.logger import logger


class CrimeSceneGenerator(BaseAgent):
    """Agent responsible for generating murder cases."""
    
    def __init__(self):
        super().__init__(
            name="Crime Scene Generator",
            role="Case Creator",
            model_type="primary"
        )
        self.system_prompt = """You are a master crime writer creating challenging murder mysteries.

CRITICAL RULES FOR CHALLENGING GAMEPLAY:
1. The killer should NOT be obvious - give multiple suspects plausible motives
2. Clues should be CIRCUMSTANTIAL, not direct - no "fingerprints on the murder weapon"
3. The killer should be SMART - they've tried to cover their tracks
4. Red herrings should be BELIEVABLE - they should make other suspects look guilty
5. Players should need to CONNECT MULTIPLE clues to solve it
6. The murder method should be consistent but clues should be subtle
7. Clue descriptions should be VAGUE about OWNERSHIP but SPECIFIC about DETAILS
   Example: "A size 9 footprint" (specific detail, vague owner)
   Example: "A black wool thread" (specific material, vague owner)
   Example: "A receipt from a hardware store" (specific document, vague owner)

VARY THE TYPES OF CLUES:
- Physical: footprints, fabric threads, fibers, blood spatter patterns, broken objects
- Document: receipts, letters, emails, notes, financial records
- Digital: phone records, security footage, text messages
- Witness: statements from different people (inconsistent details)

Make the mystery challenging but solvable through logical deduction."""
    
    async def generate_case(
        self,
        num_suspects: int = 4,
        num_witnesses: int = 2,
        theme: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a complete murder case."""
        
        # Randomly select murder method
        methods = ["gunshot", "stabbing", "poisoning", "blunt force", "strangulation"]
        method = random.choice(methods)
        
        method_descriptions = {
            "gunshot": "single gunshot wound to the chest",
            "stabbing": "multiple stab wounds to the chest", 
            "poisoning": "poison administered in a drink",
            "blunt force": "blunt force trauma to the head",
            "strangulation": "strangulation with a rope or hands"
        }
        
        # Randomly select a theme for this case
        themes = ["financial", "jealousy", "revenge", "blackmail", "inheritance", "affair"]
        case_theme = random.choice(themes)
        
        prompt = f"""Create a CHALLENGING murder mystery with the following parameters:
        - Number of suspects: {num_suspects}
        - Number of witnesses: {num_witnesses}
        - Theme: {case_theme}
        - MURDER METHOD: {method.upper()} - The victim was killed by {method_descriptions[method]}
        
        IMPORTANT RULES FOR A CHALLENGING MYSTERY:
        1. Give at least 3 suspects STRONG motives - don't make it obvious who the killer is
        2. The killer should have a plausible alibi that they've prepared
        3. Clues should be CIRCUMSTANTIAL - things that suggest guilt but don't prove it alone
        4. Red herrings should point to INNOCENT suspects to mislead
        5. The true killer should be someone who seems helpful or trustworthy
        6. No direct evidence like fingerprints on the murder weapon - the killer is smart
        
        VARY THE TYPES OF CLUES:
        Use different types of evidence:
        - Physical: footprints (mention size), fabric (mention color/material), blood spatter, broken items
        - Document: receipts, letters, emails, financial records, notes
        - Digital: phone records, security footage, text messages
        - Witness: statements with inconsistencies
        
        Each clue should have a SPECIFIC detail that players can investigate:
        - Footprint: size (e.g., "A size 10 footprint")
        - Fabric: color/material (e.g., "A blue silk thread")
        - Document: what it proves (e.g., "A receipt dated the day before")
        - Digital: timing (e.g., "A phone call at 9:47 PM")
        - Witness: what they saw (e.g., "A witness saw someone in a dark coat")
        
        Return the case as a JSON object:
        {{
            "case_title": "Title of the case",
            "case_description": "Brief description",
            "method": "{method}",
            "cause_of_death": "{method_descriptions[method]}",
            "theme": "{case_theme}",
            "victim": {{
                "name": "Victim's name",
                "age": 0,
                "occupation": "Their occupation",
                "background": "Brief background"
            }},
            "suspects": [
                {{
                    "name": "Suspect name",
                    "role": "Relationship to victim",
                    "personality": "Personality description",
                    "backstory": "Why they might have motive",
                    "alibi": "Their alibi",
                    "secrets": ["Secret that makes them look guilty"],
                    "is_killer": false
                }}
            ],
            "witnesses": [
                {{
                    "name": "Witness name",
                    "statement": "What they saw (can be vague)",
                    "credibility": 0.8,
                    "additional_info": "Extra info"
                }}
            ],
            "true_killer_id": "index of the killer (make it someone who seems less obvious)",
            "motive": "The killer's true motive",
            "timeline": [
                {{"time": "10:00 PM", "event": "Event description"}}
            ],
            "clues": [
                {{
                    "name": "Short 2-4 word label for evidence panel (e.g. 'Size 9 Footprint', 'Black Wool Thread', 'Hardware Receipt')",
                    "description": "A specific physical/digital/document clue with detail (e.g., 'A size 9 footprint', 'A blue silk thread', 'A receipt from XYZ store')",
                    "type": "physical/document/digital"
                }},
                {{
                    "name": "Short 2-4 word label for evidence panel",
                    "description": "Another different type of clue with specific detail",
                    "type": "physical/document/digital"
                }}
            ],
            "red_herrings": [
                {{
                    "name": "Short 2-4 word label for evidence panel (e.g. 'Blue Silk Fragment', 'Torn Letter')",
                    "description": "A misleading clue with specific details that point to an innocent suspect",
                    "type": "physical/document/digital"
                }}
            ]
        }}
        
        Make the mystery challenging but solvable with careful deduction.
        VARY the types of clues - don't use the same type twice!"""
        
        response = await self._call_llm(
            prompt=prompt,
            temperature=0.8,
            max_tokens=2048
        )
        
        try:
            case_data = self._parse_case_response(response.content)
            case_data["method"] = method
            case_data["cause_of_death"] = method_descriptions[method]
            case_data["theme"] = case_theme
            logger.info(f"Generated case: {case_data['case_title']} (Method: {method}, Theme: {case_theme})")
            return case_data
        except Exception as e:
            logger.error(f"Error parsing case: {str(e)}")
            return self._get_fallback_case(method)
    
    def _parse_case_response(self, response: str) -> Dict[str, Any]:
        """Parse the JSON response from the LLM."""
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return json.loads(response)
    
    def _derive_clue_name(self, description: str) -> str:
        """Derive a short 2-4 word display name from a clue description as fallback."""
        # Strip leading article ("A ", "An ", "The ")
        stripped = re.sub(r'^(a|an|the)\s+', '', description, flags=re.IGNORECASE).strip()
        # Take first 4 words, title-case them
        words = stripped.split()[:4]
        return ' '.join(w.capitalize() for w in words)
    
    def _get_fallback_case(self, method: str = "poisoning") -> Dict[str, Any]:
        """Return a fallback case with varied clue types."""
        return {
            "case_title": "The Shadow of Deception",
            "case_description": "A wealthy businessman was found dead in suspicious circumstances.",
            "method": method,
            "cause_of_death": "poison administered in a drink",
            "theme": "financial",
            "victim": {
                "name": "Richard Langley",
                "age": 55,
                "occupation": "Businessman",
                "background": "Built a business empire from nothing"
            },
            "suspects": [
                {
                    "name": "Emily Langley",
                    "role": "Daughter",
                    "personality": "Ambitious, resentful, calculating",
                    "backstory": "Felt entitled to inheritance, was cut from the will",
                    "alibi": "Was in her room reading",
                    "secrets": ["She was planning to contest the will"],
                    "is_killer": False
                },
                {
                    "name": "James Parker",
                    "role": "Business Partner",
                    "personality": "Charming, greedy, manipulative",
                    "backstory": "Was being investigated for embezzlement by the victim",
                    "alibi": "Was at a business meeting (unverified)",
                    "secrets": ["He had been stealing from the company"],
                    "is_killer": True
                },
                {
                    "name": "Sarah Lee",
                    "role": "Personal Assistant",
                    "personality": "Loyal, nervous, secretive",
                    "backstory": "Had access to all of the victim's affairs",
                    "alibi": "Was running errands",
                    "secrets": ["She was having an affair with James Parker"],
                    "is_killer": False
                },
                {
                    "name": "Michael Brown",
                    "role": "Childhood Friend",
                    "personality": "Bitter, jealous, resentful",
                    "backstory": "Was deeply in debt after investing in a failed venture",
                    "alibi": "Was at a bar (can be verified)",
                    "secrets": ["He asked Richard for money and was refused"],
                    "is_killer": False
                }
            ],
            "witnesses": [
                {
                    "name": "Thomas, the Butler",
                    "statement": "I saw someone near the study around 9:30 PM, but I couldn't see who",
                    "credibility": 0.7,
                    "additional_info": "He's elderly and his eyesight isn't great"
                }
            ],
            "true_killer_id": 1,  # James Parker
            "motive": "James poisoned Richard to stop the embezzlement investigation before he was exposed",
            "timeline": [
                {"time": "8:00 PM", "event": "Dinner at the mansion"},
                {"time": "9:00 PM", "event": "Richard retires to his study"},
                {"time": "9:30 PM", "event": "Thomas sees someone near the study"},
                {"time": "10:00 PM", "event": "Richard is found dead"},
                {"time": "10:15 PM", "event": "Police arrive"}
            ],
            "clues": [
                {"name": "Size 10 Footprint", "description": "A size 10 footprint found in the garden near the study window", "type": "physical"},
                {"name": "Black Wool Thread", "description": "A black wool thread caught on a bush near the garden path", "type": "physical"},
                {"name": "Chemical Supply Receipt", "description": "A receipt from a chemical supply store found in the trash dated the day before", "type": "document"}
            ],
            "red_herrings": [
                {"name": "Blue Silk Fragment", "description": "A torn piece of blue silk fabric found near the body", "type": "physical"},
                {"name": "Inheritance Note", "description": "A note in the victim's handwriting about cutting Emily from the will", "type": "document"},
                {"name": "Lipstick Glass", "description": "A glass with red lipstick marks found in the study", "type": "physical"}
            ]
        }
    
    def create_game_state_from_case(self, case_data: Dict[str, Any]) -> GameState:
        """Convert case data to a GameState object."""
        
        suspects = []
        for i, suspect_data in enumerate(case_data.get("suspects", [])):
            suspects.append(Suspect(
                id=f"s{i+1}",
                name=suspect_data["name"],
                role=suspect_data["role"],
                personality=suspect_data["personality"],
                backstory=suspect_data["backstory"],
                alibi=suspect_data["alibi"],
                secrets=suspect_data.get("secrets", []),
                is_killer=suspect_data.get("is_killer", False)
            ))
        
        witnesses = []
        for i, witness_data in enumerate(case_data.get("witnesses", [])):
            witnesses.append(Witness(
                id=f"w{i+1}",
                name=witness_data["name"],
                statement=witness_data["statement"],
                credibility=witness_data.get("credibility", 0.7),
                additional_info=witness_data.get("additional_info")
            ))
        
        killer_id = None
        for suspect in suspects:
            if suspect.is_killer:
                killer_id = suspect.id
                break
        
        clues = []
        # Add clues (circumstantial)
        for clue_data in case_data.get("clues", []):
            clues.append(Clue(
                id=f"c{len(clues)+1}",
                name=clue_data.get("name", "") or self._derive_clue_name(clue_data["description"]),
                description=clue_data["description"],
                type=clue_data.get("type", "physical"),
                is_red_herring=False,
                discovered=False
            ))
        
        # Add red herrings (misleading)
        for herring_data in case_data.get("red_herrings", []):
            clues.append(Clue(
                id=f"c{len(clues)+1}",
                name=herring_data.get("name", "") or self._derive_clue_name(herring_data["description"]),
                description=herring_data["description"],
                type=herring_data.get("type", "physical"),
                is_red_herring=True,
                discovered=False
            ))
        
        # Create GameState with theme included
        return GameState(
            case_title=case_data.get("case_title", "Untitled Mystery"),
            case_description=case_data.get("case_description", ""),
            theme=case_data.get("theme", "unknown"),  # Added theme field
            victim=case_data.get("victim", {}),
            suspects=suspects,
            witnesses=witnesses,
            true_killer_id=killer_id,
            motive=case_data.get("motive", ""),
            timeline=case_data.get("timeline", []),
            discovered_clues=clues
        )
    
    async def process(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a request to generate a case."""
        
        action = input_data.get("action", "generate_case")
        
        if action == "generate_case":
            num_suspects = input_data.get("num_suspects", 4)
            num_witnesses = input_data.get("num_witnesses", 2)
            theme = input_data.get("theme")
            
            case_data = await self.generate_case(num_suspects, num_witnesses, theme)
            game_state = self.create_game_state_from_case(case_data)
            
            return {
                "status": "success",
                "case_data": case_data,
                "game_state": game_state
            }
        else:
            return {
                "status": "error",
                "message": f"Unknown action: {action}"
            }