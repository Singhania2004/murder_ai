"""Test Suspect Agent."""

import asyncio
from app.agents.crime_scene_generator import CrimeSceneGenerator
from app.agents.suspect import SuspectAgent
from app.utils.logger import logger


async def test_suspect_interrogation():
    """Test suspect agent interrogation."""
    logger.info("Testing Suspect Agent...")
    
    # First generate a case
    generator = CrimeSceneGenerator()
    case_data = await generator.generate_case(num_suspects=4)
    game_state = generator.create_game_state_from_case(case_data)
    
    # Get a suspect (not the killer for first test)
    suspect_data = game_state.suspects[0]  # First suspect
    
    logger.info(f"Interrogating suspect: {suspect_data.name}")
    logger.info(f"Role: {suspect_data.role}")
    logger.info(f"Is killer? {suspect_data.is_killer}")
    
    # Create suspect agent
    suspect_agent = SuspectAgent(suspect_data, game_state)
    
    # Ask questions
    questions = [
        "Where were you at the time of the murder?",
        "Can anyone verify your alibi?",
        "What was your relationship with the victim?",
        "Did you have any disagreements with the victim?"
    ]
    
    for i, question in enumerate(questions, 1):
        logger.info(f"\n❓ Question {i}: {question}")
        response = await suspect_agent.interrogate(question)
        logger.info(f"💬 {suspect_data.name}: {response}")
    
    # Test presenting evidence
    logger.info("\n🔍 Presenting evidence...")
    response = await suspect_agent.interrogate(
        "We found a letter with your handwriting threatening the victim. Explain this.",
        evidence_presented=["A threatening letter with your handwriting"]
    )
    logger.info(f"💬 {suspect_data.name}: {response}")
    
    logger.info("\n🎉 Test complete!")


async def test_killer_interrogation():
    """Test interrogating the killer."""
    logger.info("\n" + "="*50)
    logger.info("Testing Killer Interrogation")
    logger.info("="*50)
    
    # Generate a case
    generator = CrimeSceneGenerator()
    case_data = await generator.generate_case(num_suspects=4)
    game_state = generator.create_game_state_from_case(case_data)
    
    # Find the killer
    killer_data = None
    for suspect in game_state.suspects:
        if suspect.is_killer:
            killer_data = suspect
            break
    
    if not killer_data:
        logger.error("No killer found in case!")
        return
    
    logger.info(f"Interrogating the KILLER: {killer_data.name}")
    logger.info(f"Role: {killer_data.role}")
    
    # Create suspect agent
    suspect_agent = SuspectAgent(killer_data, game_state)
    
    # Try to catch them in a lie
    questions = [
        "Where were you at the time of the murder?",
        "Can you prove your alibi?",
        "We found a blood-stained handkerchief with your initials. Can you explain this?"
    ]
    
    for question in questions:
        logger.info(f"\n❓ {question}")
        response = await suspect_agent.interrogate(question)
        logger.info(f"💬 {killer_data.name}: {response}")
    
    logger.info("\n🎉 Test complete!")


async def main():
    await test_suspect_interrogation()
    await test_killer_interrogation()


if __name__ == "__main__":
    asyncio.run(main())