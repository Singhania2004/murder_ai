"""Test Crime Scene Generator Agent."""

import asyncio
from app.agents.crime_scene_generator import CrimeSceneGenerator
from app.utils.logger import logger


async def test_generate_case():
    """Test case generation."""
    logger.info("Testing Crime Scene Generator...")
    
    generator = CrimeSceneGenerator()
    
    # Generate a case
    case_data = await generator.generate_case(
        num_suspects=4,
        num_witnesses=2,
        theme="Victorian mansion"
    )
    
    logger.info(f"✅ Case generated: {case_data['case_title']}")
    logger.info(f"   Description: {case_data['case_description']}")
    logger.info(f"   Suspects: {len(case_data['suspects'])}")
    logger.info(f"   Witnesses: {len(case_data['witnesses'])}")
    logger.info(f"   Clues: {len(case_data.get('clues', []))}")
    
    # Create game state
    game_state = generator.create_game_state_from_case(case_data)
    logger.info(f"✅ Game state created:")
    logger.info(f"   Game ID: {game_state.game_id}")
    logger.info(f"   Suspects: {len(game_state.suspects)}")
    logger.info(f"   Killer: {game_state.true_killer_id}")
    
    # Print suspect details
    logger.info("\n📋 Suspects:")
    for suspect in game_state.suspects:
        logger.info(f"   - {suspect.name} ({suspect.role})")
        logger.info(f"     Alibi: {suspect.alibi}")
        logger.info(f"     Killer: {suspect.is_killer}")
    
    logger.info("\n🎉 Test complete!")


async def main():
    await test_generate_case()


if __name__ == "__main__":
    asyncio.run(main())