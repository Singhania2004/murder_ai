"""LangGraph node implementations."""

from typing import Dict, Any, List
from app.agents.crime_scene_generator import CrimeSceneGenerator
from app.agents.suspect import SuspectAgent
from app.agents.forensic_expert import ForensicExpert
from app.agents.game_master import GameMaster
from app.langgraph.state import AgentState
from app.utils.logger import logger


class NodeHandler:
    """Handler for all LangGraph nodes."""
    
    def __init__(self):
        self.crime_scene_gen = CrimeSceneGenerator()
        self.forensic_expert = ForensicExpert()
        self.game_master = GameMaster()
        self.suspect_agents = {}
    
    async def generate_case_node(self, state: AgentState) -> Dict[str, Any]:
        """Generate a new case."""
        logger.info("🔄 Generating new case...")
        
        try:
            case_data = await self.crime_scene_gen.generate_case(
                num_suspects=4,
                num_witnesses=2
            )
            game_state = self.crime_scene_gen.create_game_state_from_case(case_data)
            
            intro = await self.game_master.get_intro(game_state)
            
            self.suspect_agents.clear()
            
            return {
                "game_state": game_state,
                "response": intro,
                "current_action": "intro",
                "next_node": "awaiting_input",
                "game_complete": False
            }
            
        except Exception as e:
            logger.error(f"Error generating case: {str(e)}")
            return {
                "error": f"Failed to generate case: {str(e)}",
                "next_node": "error"
            }
    
    async def interrogate_suspect_node(self, state: AgentState) -> Dict[str, Any]:
        """Interrogate a suspect."""
        game_state = state["game_state"]
        suspect_id = state.get("suspect_id")
        question = state.get("user_input")
        evidence = state.get("evidence_presented", [])
        
        if not suspect_id or not question:
            return {
                "error": "Missing suspect_id or question",
                "next_node": "awaiting_input"
            }
        
        suspect = game_state.get_suspect(suspect_id)
        if not suspect:
            return {
                "error": f"Suspect {suspect_id} not found",
                "next_node": "awaiting_input"
            }
        
        agent_key = f"{game_state.game_id}_{suspect_id}"
        if agent_key not in self.suspect_agents:
            self.suspect_agents[agent_key] = SuspectAgent(suspect, game_state)
        
        suspect_agent = self.suspect_agents[agent_key]
        suspect_agent.update_context(game_state)
        
        try:
            response = await suspect_agent.interrogate(question, evidence)
            
            game_state.mark_suspect_interrogated(suspect_id)
            
            game_state.chat_history.append({
                "role": "detective",
                "content": f"Asked {suspect.name}: {question}"
            })
            game_state.chat_history.append({
                "role": suspect.name,
                "content": response
            })
            
            # Return ONLY the suspect's response, not the duplicate narrative
            return {
                "game_state": game_state,
                "response": f"**{suspect.name}**: {response}",
                "next_node": "awaiting_input"
            }
            
        except Exception as e:
            logger.error(f"Error in interrogation: {str(e)}")
            return {
                "error": f"Failed to interrogate: {str(e)}",
                "next_node": "awaiting_input"
            }
    
    async def analyze_evidence_node(self, state: AgentState) -> Dict[str, Any]:
        """Analyze evidence."""
        game_state = state["game_state"]
        clue_id = state.get("clue_id")
        
        if not clue_id:
            return {
                "error": "Missing clue_id",
                "next_node": "awaiting_input"
            }
        
        clue = game_state.get_clue(clue_id)
        if not clue:
            return {
                "error": f"Clue {clue_id} not found",
                "next_node": "awaiting_input"
            }
        
        try:
            result = await self.forensic_expert.analyze_evidence(clue, game_state)
            
            clue.analyzed = True
            clue.discovered = True
            
            game_state.chat_history.append({
                "role": "detective",
                "content": f"Analyzed evidence: {clue.description}"
            })
            game_state.chat_history.append({
                "role": "forensic_expert",
                "content": result["analysis"]
            })
            
            # Rebuild suspect facts after analysis (in case new clues were discovered)
            game_state.build_suspect_facts()
            
            return {
                "game_state": game_state,
                "response": f"**Forensic Analysis**: {result['analysis']}",
                "next_node": "awaiting_input"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing evidence: {str(e)}")
            return {
                "error": f"Failed to analyze evidence: {str(e)}",
                "next_node": "awaiting_input"
            }
    
    async def discover_evidence_node(self, state: AgentState) -> Dict[str, Any]:
        """Discover new evidence - atmospheric and vague, never reveals clue specifics."""
        game_state = state["game_state"]
        search_area = state.get("user_input", "the crime scene")
        
        try:
            undiscovered = [c for c in game_state.discovered_clues if not c.discovered]
            
            if not undiscovered:
                return {
                    "game_state": game_state,
                    "response": "🔎 You've combed through every corner. There's nothing left to find here.",
                    "new_clues": [],
                    "next_node": "awaiting_input"
                }
            
            new_clues = undiscovered[:1]
            clue = new_clues[0]
            clue.discovered = True
            
            # Generate a narrative that mentions the general item found without the forensic details
            prompt = f"""Write a 1-2 sentence atmospheric discovery narrative for a detective searching {search_area}.
            
The clue details are: "{clue.description}"

RULES:
1. Mention the general item that was found and where it was found (e.g. a receipt in the trash, a footprint in the dirt/garden, CCTV camera footage, a thread caught on a bush).
2. Do NOT mention any specific forensic details from the clue description, such as:
   - Specific measurements/sizes (e.g., shoe size, gsm)
   - Specific brands or store names (e.g., Sprint-X, Dunlop)
   - Specific item purchases (e.g., gun cleaning kit)
   - Specific timestamps or dates (e.g., 10:10 PM, day before)
   - Specific colors or fabric types (e.g., blue silk, black hoodie)
3. Keep it brief (under 40 words), atmospheric, and mysterious.

Example for "A size 11 footprint with a unique tread pattern was found near the crime scene":
"A faint footprint is pressed into the soft earth near the crime scene, shadowed by the brush. It's worth examining further."

Example for "A receipt from a hardware store was found in the trash, dated the day before, with a purchase of a gun cleaning kit":
"Among the crumpled papers in the trash can, you discover a discarded store receipt. It might hold some crucial answers."
"""
            
            response = await self.game_master._call_llm(
                prompt=prompt,
                temperature=0.7,
                max_tokens=80
            )
            
            # Rebuild suspect facts after discovering new clues
            game_state.build_suspect_facts()
            
            return {
                "game_state": game_state,
                "response": response.content,
                "new_clues": [c.model_dump() for c in new_clues],
                "next_node": "awaiting_input"
            }
            
        except Exception as e:
            logger.error(f"Error discovering evidence: {str(e)}")
            return {
                "error": f"Failed to discover evidence: {str(e)}",
                "next_node": "awaiting_input"
            }
    
    async def verify_alibi_node(self, state: AgentState) -> Dict[str, Any]:
        """Verify a suspect's alibi."""
        game_state = state["game_state"]
        suspect_id = state.get("suspect_id")
        
        if not suspect_id:
            return {
                "error": "Missing suspect_id",
                "next_node": "awaiting_input",
                "response": "Please select a suspect first."
            }
        
        suspect = game_state.get_suspect(suspect_id)
        if not suspect:
            return {
                "error": f"Suspect {suspect_id} not found",
                "next_node": "awaiting_input"
            }
        
        # Check if suspect has been interrogated
        if not suspect.interrogated:
            result = f"❌ {suspect.name} has not been interrogated yet. Ask them about their whereabouts first."
            
            game_state.chat_history.append({
                "role": "detective",
                "content": f"Tried to verify {suspect.name}'s alibi without interrogation"
            })
            game_state.chat_history.append({
                "role": "system",
                "content": result
            })
            
            return {
                "game_state": game_state,
                "response": f"**Alibi Verification**: {result}",
                "next_node": "awaiting_input"
            }
        
        # Check if alibi is verifiable
        if not suspect.alibi_verifiable:
            result = f"❌ {suspect.name}'s alibi cannot be verified."
            suspect.alibi_verification_result = result
            
            game_state.chat_history.append({
                "role": "detective",
                "content": f"Tried to verify {suspect.name}'s alibi"
            })
            game_state.chat_history.append({
                "role": "system",
                "content": result
            })
            
            return {
                "game_state": game_state,
                "response": f"**Alibi Verification**: {result}",
                "next_node": "awaiting_input"
            }
        
        # Generate verification result based on alibi_truth
        if suspect.alibi_truth:
            result = f"✅ {suspect.name}'s alibi has been VERIFIED: {suspect.alibi_verification_details} confirms they were telling the truth."
        else:
            result = f"❌ {suspect.name}'s alibi has been CONTRADICTED: {suspect.alibi_verification_details} shows they were NOT where they claimed to be."
        
        # Store the result
        suspect.alibi_verification_result = result
        
        game_state.chat_history.append({
            "role": "detective",
            "content": f"Verified {suspect.name}'s alibi"
        })
        game_state.chat_history.append({
            "role": "system",
            "content": result
        })
        
        return {
            "game_state": game_state,
            "response": f"**Alibi Verification**: {result}",
            "next_node": "awaiting_input"
        }
    
    async def get_hint_node(self, state: AgentState) -> Dict[str, Any]:
        """Get a hint from the game master."""
        game_state = state["game_state"]
        
        try:
            hint = await self.game_master.get_hint(game_state)
            
            return {
                "response": f"**Game Master's Hint**: {hint}",
                "next_node": "awaiting_input"
            }
            
        except Exception as e:
            logger.error(f"Error getting hint: {str(e)}")
            return {
                "error": f"Failed to get hint: {str(e)}",
                "next_node": "awaiting_input"
            }
    
    async def make_accusation_node(self, state: AgentState) -> Dict[str, Any]:
        """Process a player's accusation."""
        game_state = state["game_state"]
        suspect_name = state.get("user_input")
        motive = state.get("motive", "")
        
        if not suspect_name:
            return {
                "error": "Missing suspect name",
                "next_node": "awaiting_input"
            }
        
        try:
            result = await self.game_master.reveal_truth(
                game_state,
                suspect_name,
                motive
            )
            
            game_state.solved = True
            game_state.accusations_made += 1
            game_state.correct_accusation = result["correct"]
            game_state.phase = "VERDICT" if result["correct"] else "ACCUSATION"
            game_state.is_active = False
            
            game_state.chat_history.append({
                "role": "detective",
                "content": f"ACCUSED: {suspect_name}"
            })
            game_state.chat_history.append({
                "role": "game_master",
                "content": result["reveal"]
            })
            
            return {
                "game_state": game_state,
                "response": result["reveal"],
                "game_complete": True,
                "player_correct": result["correct"],
                "next_node": "end"
            }
            
        except Exception as e:
            logger.error(f"Error processing accusation: {str(e)}")
            return {
                "error": f"Failed to process accusation: {str(e)}",
                "next_node": "awaiting_input"
            }
    
    async def end_game_node(self, state: AgentState) -> Dict[str, Any]:
        """End the game and provide summary."""
        game_state = state["game_state"]
        
        summary = f"""
## 🎭 Game Over

**Case**: {game_state.case_title}
**Solved**: {'✅ Yes!' if game_state.solved else '❌ No'}
**Accusations Made**: {game_state.accusations_made}
"""
        
        if game_state.solved:
            summary += f"\n**Congratulations!** You solved the mystery!"
        else:
            summary += f"\n**Better luck next time!** The killer was {game_state.true_killer_id}."
        
        return {
            "response": summary,
            "game_complete": True,
            "next_node": "end"
        }