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

VARY THE TYPES OF CLUES:
- Physical: footprints, fabric threads, fibers, blood spatter patterns, broken objects
- Document: receipts, letters, emails, notes, financial records
- Digital: phone records, security footage, text messages

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
        
        # Generate random date and time
        from datetime import datetime, timedelta
        days_ago = random.randint(1, 30)
        murder_date = datetime.now() - timedelta(days=days_ago)
        date_str = murder_date.strftime("%B %d, %Y")
        
        hour = random.randint(20, 23)
        minute = random.choice([0, 15, 30, 45])
        time_str = f"{hour:02d}:{minute:02d}"
        
        # Randomly select how many clues (3-4) and red herrings (1-2)
        num_clues = random.randint(3, 4)
        # num_red_herrings = random.randint(1, 2)
        num_red_herrings = 1
        
        prompt = f"""Create a CHALLENGING murder mystery with the following parameters:
        - Number of suspects: {num_suspects}
        - Number of witnesses: {num_witnesses}
        - Theme: {case_theme}
        - MURDER METHOD: {method.upper()} - The victim was killed by {method_descriptions[method]}
        
        CASE METADATA:
        - Case Date: {date_str}
        - Estimated Time of Death: {time_str}
        
        TIME CONSISTENCY RULES:
        The generated murder time ({time_str}) is the REFERENCE POINT for the entire case.
        
        Only include timestamps when they are naturally part of the evidence.
        Examples that SHOULD have timestamps:
        - CCTV footage
        - Phone call logs
        - Receipts
        
        Examples that SHOULD NOT have timestamps:
        - Blood stains
        - Shoe prints
        - Fabric fibres
        - DNA
        - Weapon description
        
        EVIDENCE QUALITY RULES - FOLLOW CAREFULLY:
        1. Avoid vague digital evidence like "an email was sent" - these are hard to investigate further
        2. Prefer physical evidence that can be linked to suspects (clothing fibers, footprints, objects)
        3. Prefer witness testimony about specific sightings or interactions
        4. Prefer surveillance footage or call logs with specific times
        5. Make sure clues can actually be investigated by interrogating suspects
        
        GOOD EVIDENCE EXAMPLES:
        - CCTV footage shows a figure in a black jacket entering at 8:50 PM
        - A call log shows a call from a suspect's phone at 8:10 PM
        - A witness heard an argument at 7:30 PM 
        - A hidden document outlining a plan to overthrow the victim 
        - A specific clothing fiber (e.g., "A blue silk thread") found at the scene
        
        BAD EVIDENCE EXAMPLES (AVOID):
        - "An email was sent" - too vague, can't investigate further
        - "A text message was received" - no way to verify who sent it
        - "A note was found" - unless it has specific handwriting that can be matched
        
        IMPORTANT: You need {num_clues} clues and {num_red_herrings} red herrings.
        Total evidence items: {num_clues + num_red_herrings}
        
        Return the case as a JSON object:
        {{
            "case_title": "Title of the case",
            "case_description": "Brief description of the case (2-3 sentences)",
            "method": "{method}",
            "cause_of_death": "{method_descriptions[method]}",
            "theme": "{case_theme}",
            "case_date": "{date_str}",
            "murder_time": "{time_str}",
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
                    "alibi": "Their alibi (can include time references)",
                    "secrets": ["Secret that makes them look guilty"],
                    "is_killer": false
                }}
            ],
            "witnesses": [
                {{
                    "name": "Witness name",
                    "statement": "What they saw (can be vague)",
                    "credibility": 0.8,
                    "additional_info": "Extra info",
                    "connected_to": "Which suspect this witness can verify",
                    "connection_type": "alibi_verification"
                }}
            ],
            "true_killer_id": "index of the killer (make it someone who seems less obvious)",
            "motive": "The killer's true motive",
            "clues": [
                {{
                    "name": "Short 2-4 word label",
                    "description": "A specific, actionable clue",
                    "type": "physical/document/digital"
                }},
                // Add {num_clues - 1} more clues (total of {num_clues})
            ],
            "red_herrings": [
                {{
                    "name": "Short 2-4 word label",
                    "description": "A misleading clue that points to an innocent suspect",
                    "type": "physical/document/digital"
                }},
                // Add {num_red_herrings - 1} more red herrings (total of {num_red_herrings})
            ]
        }}
        
        Make the mystery challenging but solvable with careful deduction.
        Ensure clues are SPECIFIC and INVESTIGATABLE."""
        
        response = await self._call_llm(
            prompt=prompt,
            temperature=0.8,
            max_tokens=2048
        )
        
        try:
            case_data = self._parse_case_response(response.content)
            # Ensure the generated date/time are used
            case_data["case_date"] = date_str
            case_data["murder_time"] = time_str
            case_data["method"] = method
            case_data["cause_of_death"] = method_descriptions[method]
            case_data["theme"] = case_theme
            
            # Log the number of clues and red herrings
            logger.info(f"Generated case: {case_data['case_title']} (Date: {date_str}, Time: {time_str})")
            logger.info(f"Clues: {len(case_data.get('clues', []))}, Red Herrings: {len(case_data.get('red_herrings', []))}")
            return case_data
        except Exception as e:
            logger.error(f"Error parsing case: {str(e)}")
            raise ValueError(f"Failed to generate valid case: {str(e)}")
    
    def _parse_case_response(self, response: str) -> Dict[str, Any]:
        """Parse the JSON response from the LLM."""
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return json.loads(response)
    
    def _derive_clue_name(self, description: str) -> str:
        """Derive a short 2-4 word display name from a clue description as fallback."""
        stripped = re.sub(r'^(a|an|the)\s+', '', description, flags=re.IGNORECASE).strip()
        words = stripped.split()[:4]
        return ' '.join(w.capitalize() for w in words)
    
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
                additional_info=witness_data.get("additional_info"),
                connected_to=witness_data.get("connected_to"),
                connection_type=witness_data.get("connection_type")
            ))
        
        killer_id = None
        for suspect in suspects:
            if suspect.is_killer:
                killer_id = suspect.id
                break
        
        clues = []
        for clue_data in case_data.get("clues", []):
            clues.append(Clue(
                id=f"c{len(clues)+1}",
                name=clue_data.get("name", "") or self._derive_clue_name(clue_data["description"]),
                description=clue_data["description"],
                type=clue_data.get("type", "physical"),
                is_red_herring=False,
                discovered=False
            ))
        
        for herring_data in case_data.get("red_herrings", []):
            clues.append(Clue(
                id=f"c{len(clues)+1}",
                name=herring_data.get("name", "") or self._derive_clue_name(herring_data["description"]),
                description=herring_data["description"],
                type=herring_data.get("type", "physical"),
                is_red_herring=True,
                discovered=False
            ))
        
        return GameState(
            case_title=case_data.get("case_title", "Untitled Mystery"),
            case_description=case_data.get("case_description", ""),
            theme=case_data.get("theme", "unknown"),
            case_date=case_data.get("case_date", ""),
            murder_time=case_data.get("murder_time", ""),
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