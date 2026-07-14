"""Test Game Master Agent."""

import asyncio
from app.agents.crime_scene_generator import CrimeSceneGenerator
from app.agents.game_master import GameMaster
from app.utils.logger import logger


async def test_game_master():
    """Test Game Master agent."""
    logger.info("\n" + "="*50)
    logger.info("Testing Game Master")
    logger.info("="*50)
    
    # Generate a case
    generator = CrimeSceneGenerator()
    case_data = await generator.generate_case(num_suspects=4)
    game_state = generator.create_game_state_from_case(case_data)
    
    # Create Game Master
    gm = GameMaster()
    
    # Test intro
    logger.info("\n📖 Game Master Introduction:")
    intro = await gm.get_intro(game_state)
    logger.info(f"{intro}\n")
    
    # Test hint (before investigation)
    logger.info("\n💡 Game Master Hint:")
    hint = await gm.get_hint(game_state)
    logger.info(f"{hint}\n")
    
    # Simulate some investigation
    game_state.phase = "INVESTIGATION"
    game_state.suspects[0].interrogated = True
    game_state.discovered_clues[0].discovered = True
    
    # Test reaction to action
    logger.info("\n🎭 Game Master Reaction:")
    reaction = await gm.react_to_action(
        "Interrogated a suspect",
        game_state,
        "The detective questioned Emma Langley about her alibi."
    )
    logger.info(f"{reaction}\n")
    
    # Test reveal (wrong guess)
    logger.info("\n🔍 Game Master Reveal (Wrong Guess):")
    result = await gm.reveal_truth(game_state, "Wrong Person")
    logger.info(f"Correct: {result['correct']}")
    logger.info(f"Killer: {result['killer']}")
    logger.info(f"Reveal: {result['reveal']}\n")
    
    # Test reveal (correct guess)
    killer_name = None
    for suspect in game_state.suspects:
        if suspect.is_killer:
            killer_name = suspect.name
            break
    
    if killer_name:
        logger.info(f"\n🔍 Game Master Reveal (Correct Guess: {killer_name}):")
        result = await gm.reveal_truth(game_state, killer_name)
        logger.info(f"Correct: {result['correct']}")
        logger.info(f"Reveal: {result['reveal']}\n")
    
    logger.info("✅ Game Master test complete!")


async def main():
    await test_game_master()


if __name__ == "__main__":
    asyncio.run(main())