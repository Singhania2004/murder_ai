"""Game Master Agent - Orchestrates the entire game."""

from typing import Dict, Any, Optional, List
from app.agents.base import BaseAgent
from app.models.state import GameState, Suspect, Clue
from app.utils.logger import logger


class GameMaster(BaseAgent):
    """The Game Master - orchestrates the murder mystery game."""
    
    def __init__(self):
        super().__init__(
            name="Game Master",
            role="Orchestrator",
            model_type="primary"
        )
        self.system_prompt = """You are the Game Master for a murder mystery detective game.
        
Your role is to:
1. Orchestrate the flow of the game
2. Provide narrative descriptions and context
3. React to player actions
4. Reveal the truth at the end
5. Maintain tension and engagement
6. Give subtle hints when the player is stuck

You know the absolute truth about the case:
- Who the killer is
- The motive
- The timeline
- All secrets

Rules:
- Never reveal the killer directly unless the player solves it
- Be cryptic but fair
- Drop subtle hints when the player is stuck
- Maintain narrative consistency
- Make the experience immersive and engaging"""
    
    async def get_intro(self, game_state: GameState) -> str:
        """Get the introduction narrative for the case."""
        
        prompt = f"""You are the Game Master. Introduce this murder mystery case to the detective:

CASE: {game_state.case_title}
DESCRIPTION: {game_state.case_description}
VICTIM: {game_state.victim.get('name', 'Unknown')}
SUSPECTS: {', '.join([s.name for s in game_state.suspects])}

Write a dramatic, engaging introduction that:
1. Sets the scene
2. Describes the victim
3. Mentions the suspects
4. Establishes the mood
5. Gives the detective their mission

Keep it immersive and mysterious."""
        
        response = await self._call_llm(
            prompt=prompt,
            temperature=0.8,
            max_tokens=1024
        )
        
        return response.content
    
    async def get_hint(self, game_state: GameState) -> str:
        """Give a context-aware, tiered hint to help the player progress."""
        
        discovered = [c for c in game_state.discovered_clues if c.discovered]
        analyzed = [c for c in discovered if c.analyzed]
        undiscovered = [c for c in game_state.discovered_clues if not c.discovered]
        unanalyzed = [c for c in discovered if not c.analyzed]
        interrogated = [s for s in game_state.suspects if s.interrogated]
        
        # Tier 1: Nothing found yet
        if not discovered:
            return (
                "The crime scene holds its secrets patiently. "
                "You won't find answers standing here — search the area for physical evidence. "
                "Start where the body was found."
            )
        
        # Tier 2: Evidence found but none analyzed
        if unanalyzed and not analyzed:
            clue = unanalyzed[0]
            return (
                f"You've collected evidence but haven't examined it yet. "
                f"The forensic lab can tell you far more than your eyes alone. "
                f"Have the {'physical' if clue.type == 'physical' else clue.type} evidence analyzed before drawing conclusions."
            )
        
        # Tier 3: Evidence analyzed but no interrogations done
        if analyzed and not interrogated:
            analyzed_clue = analyzed[0]
            return (
                f"The forensic report is in — you now know things the suspects don't know you know. "
                f"Use that. Pick a suspect and start asking questions. "
                f"The evidence doesn't lie, but people do."
            )
        
        # Tier 4: Some interrogations, more clues undiscovered
        if undiscovered and interrogated:
            return (
                "You've spoken to some of the suspects, but you haven't found all the evidence yet. "
                "There may be clues still hidden at the scene. "
                "Search again — investigators who stop too early miss the truth."
            )
        
        # Tier 5: All clues found and analyzed, partial interrogations
        not_interrogated = [s for s in game_state.suspects if not s.interrogated]
        if not_interrogated and analyzed:
            name = not_interrogated[0].name
            return (
                f"You haven't spoken to everyone yet. "
                f"{name} has been waiting — and silent people in a murder investigation are rarely innocent of *something*. "
                f"Push them."
            )
        
        # Tier 6: All suspects interrogated — look for contradictions
        killer = next((s for s in game_state.suspects if s.is_killer), None)
        
        prompt = f"""The detective has interrogated all suspects and found all the evidence. Help them identify a contradiction.

CASE: {game_state.case_title}
ANALYZED EVIDENCE: {', '.join([c.description for c in analyzed])}
SUSPECTS: {', '.join([s.name for s in game_state.suspects])}
TRUE KILLER: {killer.name if killer else 'Unknown'}

Give a SUBTLE cryptic hint (2 sentences max) that:
1. Points to a specific contradiction or overlooked detail WITHOUT naming the killer
2. Makes the detective re-examine something they might have dismissed
3. Is mysterious but genuinely useful

Do not name the killer directly."""
        
        response = await self._call_llm(
            prompt=prompt,
            temperature=0.7,
            max_tokens=120
        )
        
        return response.content
    
    async def react_to_action(
        self,
        action: str,
        game_state: GameState,
        details: Optional[str] = None
    ) -> str:
        """React to a player action."""
        
        prompt = f"""The detective has taken an action in the investigation:

ACTION: {action}
{details if details else ""}

CURRENT STATE:
- Phase: {game_state.phase}
- Discovered Clues: {len([c for c in game_state.discovered_clues if c.discovered])}
- Interrogated Suspects: {', '.join([s.name for s in game_state.suspects if s.interrogated])}
- Accusations Made: {game_state.accusations_made}

As the Game Master, respond to this action with:
1. A narrative description of what happens
2. Any new information revealed
3. The reaction of characters involved
4. Progress update on the investigation

Keep it dramatic and engaging."""
        
        response = await self._call_llm(
            prompt=prompt,
            temperature=0.7,
            max_tokens=512
        )
        
        return response.content
    
    async def reveal_truth(
        self,
        game_state: GameState,
        player_guess: Optional[str] = None,
        player_motive: Optional[str] = None
    ) -> Dict[str, Any]:
        """Reveal the truth at the end of the game."""
        
        # Find the killer
        killer = None
        for suspect in game_state.suspects:
            if suspect.is_killer:
                killer = suspect
                break
        
        if not killer:
            return {
                "status": "error",
                "message": "No killer found in the case!"
            }
        
        # Check if player guessed correctly
        correct = False
        if player_guess:
            correct = player_guess.lower().strip() == killer.name.lower().strip()
        
        prompt = f"""You are the Game Master revealing the truth of the murder mystery.

    CASE: {game_state.case_title}
    TRUE KILLER: {killer.name} ({killer.role})
    MOTIVE: {game_state.motive}
    PLAYER GUESSED: {player_guess if player_guess else "No guess made"}
    PLAYER WAS {'CORRECT' if correct else 'INCORRECT'}

    Provide a CONCISE verdict (max 150 words) that:
    1. States whether the player was correct or not
    2. Names the killer and their motive
    3. Briefly explains how the murder was committed

    Format the response like this:
    VERDICT: [Correct/Incorrect]
    KILLER: [Name]
    MOTIVE: [Brief motive]
    DETAILS: [Brief explanation of how it happened]

    Keep it clear and dramatic but concise."""
        
        response = await self._call_llm(
            prompt=prompt,
            temperature=0.7,
            max_tokens=300
        )
        
        return {
            "status": "success",
            "correct": correct,
            "killer": killer.name,
            "killer_role": killer.role,
            "motive": game_state.motive,
            "reveal": response.content
        }
    
    async def process(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a Game Master request."""
        
        action = input_data.get("action", "intro")
        game_state = input_data.get("game_state")
        
        if not game_state:
            return {
                "status": "error",
                "message": "Missing game_state"
            }
        
        if action == "intro":
            content = await self.get_intro(game_state)
            return {"status": "success", "content": content}
        
        elif action == "hint":
            content = await self.get_hint(game_state)
            return {"status": "success", "content": content}
        
        elif action == "react":
            action_type = input_data.get("action_type", "")
            details = input_data.get("details", "")
            content = await self.react_to_action(action_type, game_state, details)
            return {"status": "success", "content": content}
        
        elif action == "reveal":
            player_guess = input_data.get("guess")
            player_motive = input_data.get("motive")
            result = await self.reveal_truth(game_state, player_guess, player_motive)
            return result
        
        else:
            return {
                "status": "error",
                "message": f"Unknown action: {action}"
            }