"""Test Forensic Expert and Witness agents."""

import asyncio
from app.agents.crime_scene_generator import CrimeSceneGenerator
from app.agents.forensic_expert import ForensicExpert
from app.agents.witness import WitnessAgent
from app.utils.logger import logger


async def test_forensic_expert():
    """Test forensic expert analysis."""
    logger.info("\n" + "="*50)
    logger.info("Testing Forensic Expert")
    logger.info("="*50)
    
    # Generate a case
    generator = CrimeSceneGenerator()
    case_data = await generator.generate_case(num_suspects=4)
    game_state = generator.create_game_state_from_case(case_data)
    
    # Get some clues
    clues = game_state.discovered_clues[:3]  # First 3 clues
    
    # Create forensic expert
    forensic = ForensicExpert()
    
    for i, clue in enumerate(clues, 1):
        logger.info(f"\n🔬 Analyzing Clue {i}: {clue.description}")
        logger.info(f"   Type: {clue.type}")
        logger.info(f"   Red Herring: {clue.is_red_herring}")
        
        result = await forensic.analyze_evidence(clue, game_state)
        logger.info(f"   Analysis: {result['analysis'][:200]}...")
    
    logger.info("\n✅ Forensic Expert test complete!")


async def test_witness():
    """Test witness testimony."""
    logger.info("\n" + "="*50)
    logger.info("Testing Witness")
    logger.info("="*50)
    
    # Generate a case
    generator = CrimeSceneGenerator()
    case_data = await generator.generate_case(num_suspects=4)
    game_state = generator.create_game_state_from_case(case_data)
    
    # Get first witness
    if not game_state.witnesses:
        logger.error("No witnesses in case!")
        return
    
    witness_data = game_state.witnesses[0]
    
    logger.info(f"Witness: {witness_data.name}")
    logger.info(f"Statement: {witness_data.statement}")
    logger.info(f"Credibility: {witness_data.credibility}")
    
    # Create witness agent
    witness = WitnessAgent(witness_data, game_state)
    
    questions = [
        "Can you tell me exactly what you saw?",
        "What time did this happen?",
        "Did you see anyone suspicious?",
        "Is there anything else you remember?"
    ]
    
    for question in questions:
        logger.info(f"\n❓ Detective: {question}")
        response = await witness.testify(question)
        logger.info(f"💬 {witness_data.name}: {response}")
    
    logger.info("\n✅ Witness test complete!")


async def main():
    await test_forensic_expert()
    await test_witness()


if __name__ == "__main__":
    asyncio.run(main())