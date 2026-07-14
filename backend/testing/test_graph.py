"""Test LangGraph integration with proper state management."""

import asyncio
from app.langgraph.graph import GameGraph
from app.utils.logger import logger


async def test_game_flow():
    """Test the complete game flow with state management."""
    logger.info("\n" + "="*50)
    logger.info("Testing LangGraph Game Flow")
    logger.info("="*50)
    
    graph = GameGraph()
    
    # Start the game
    logger.info("\n🎮 Starting new game...")
    result = await graph.start_game()
    
    game_state = result.get("game_state")
    response = result.get("response", "")
    
    logger.info(f"Response preview: {response[:300]}...")
    
    if not game_state:
        logger.error("Failed to create game state")
        logger.error(f"Error: {result.get('error')}")
        return
    
    logger.info(f"✅ Game created: {game_state.case_title}")
    logger.info(f"   Suspects: {len(game_state.suspects)}")
    logger.info(f"   Witnesses: {len(game_state.witnesses)}")
    logger.info(f"   Clues: {len(game_state.discovered_clues)}")
    
    # Get first suspect
    suspect = game_state.suspects[0]
    logger.info(f"\n🔍 Interrogating suspect: {suspect.name}")
    logger.info(f"   Role: {suspect.role}")
    logger.info(f"   Is killer? {suspect.is_killer}")
    
    result = await graph.process_action(
        action="interrogate",
        suspect_id=suspect.id,
        user_input="Where were you at the time of the murder?"
    )
    
    response = result.get("response", "")
    logger.info(f"Response preview: {response[:300]}...")
    game_state = result.get("game_state")
    
    if not game_state:
        logger.error("Game state lost during interrogation!")
        return
    
    # Get a clue
    if game_state.discovered_clues:
        # Find an undiscovered clue
        clue = None
        for c in game_state.discovered_clues:
            if not c.discovered:
                clue = c
                break
        
        if clue:
            logger.info(f"\n🔬 Analyzing clue: {clue.description}")
            logger.info(f"   Type: {clue.type}")
            logger.info(f"   Red Herring: {clue.is_red_herring}")
            
            result = await graph.process_action(
                action="analyze",
                clue_id=clue.id
            )
            
            response = result.get("response", "")
            logger.info(f"Response preview: {response[:300]}...")
            game_state = result.get("game_state")
    
    # Get a hint
    logger.info("\n💡 Getting a hint...")
    result = await graph.process_action(
        action="hint"
    )
    
    response = result.get("response", "")
    logger.info(f"Response preview: {response[:300]}...")
    game_state = result.get("game_state")
    
    # Find the killer's name
    killer_name = None
    for suspect in game_state.suspects:
        if suspect.is_killer:
            killer_name = suspect.name
            break
    
    # Make an accusation
    logger.info(f"\n⚖️ Making accusation against: {killer_name}")
    result = await graph.process_action(
        action="accuse",
        user_input=killer_name,
        motive="The evidence points to them"
    )
    
    response = result.get("response", "")
    logger.info(f"Response preview: {response[:500]}...")
    logger.info(f"Game complete: {result.get('game_complete')}")
    logger.info(f"Correct: {result.get('correct')}")
    
    logger.info("\n✅ Game flow test complete!")


async def main():
    await test_game_flow()


if __name__ == "__main__":
    asyncio.run(main())