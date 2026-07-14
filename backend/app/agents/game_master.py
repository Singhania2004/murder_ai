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
        """Give a subtle hint to help the player."""
        
        # Find what clues have been discovered
        discovered = [c.description for c in game_state.discovered_clues if c.discovered]
        
        prompt = f"""The detective is investigating this case and seems stuck.

CASE: {game_state.case_title}
DISCOVERED CLUES: {', '.join(discovered) if discovered else 'None yet'}
INTERROGATED SUSPECTS: {', '.join([s.name for s in game_state.suspects if s.interrogated])}
TRUE KILLER: {game_state.true_killer_id}

Give a subtle, cryptic hint that:
1. Doesn't reveal the killer directly
2. Points to a contradiction or overlooked detail
3. Encourages the detective to investigate further
4. Is mysterious but helpful

Keep it in character as the Game Master."""
        
        response = await self._call_llm(
            prompt=prompt,
            temperature=0.7,
            max_tokens=256
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