"""Test state manager."""

from app.models import get_db
from app.models.state import GameState, Suspect, Witness, Clue
from app.state_manager import StateManager
from app.database import init_database
from app.utils.logger import logger


def test_state_manager():
    """Test state manager operations."""
    
    # Initialize database first
    init_database()
    
    # Get DB session
    db = next(get_db())
    manager = StateManager(db)
    
    # Create a test game state
    state = GameState(
        case_title="The Murder at Sterling Manor",
        case_description="A wealthy industrialist was found dead in his study.",
        victim={"name": "Richard Sterling", "age": 65},
        suspects=[
            Suspect(
                id="s1",
                name="Eleanor Sterling",
                role="Wife",
                personality="Elegant, composed, but with a sharp tongue",
                backstory="Married to Richard for 30 years, but grew distant",
                alibi="In her room, reading",
                secrets=["She was having an affair"],
                is_killer=False
            ),
            Suspect(
                id="s2",
                name="Marcus Webb",
                role="Butler",
                personality="Loyal, detail-oriented, but nervous",
                backstory="Has worked for the family for 20 years",
                alibi="In the kitchen, preparing tea",
                secrets=["He owed Richard money for gambling debts"],
                is_killer=True
            )
        ],
        true_killer_id="s2",
        motive="Marcus killed Richard to cover up his gambling debts"
    )
    
    try:
        # Save the game
        saved_state = manager.create_game(state)
        logger.info(f"✅ Created game with ID: {saved_state.game_id}")
        
        # Retrieve the game
        retrieved_state = manager.get_game(saved_state.game_id)
        if retrieved_state:
            logger.info(f"✅ Retrieved game: {retrieved_state.case_title}")
            logger.info(f"   Number of suspects: {len(retrieved_state.suspects)}")
            logger.info(f"   True killer: {retrieved_state.true_killer_id}")
        
        # Update the game
        state.phase = "INVESTIGATION"
        state.add_clue(Clue(
            id="c1",
            description="Bloody footprint found near the body",
            type="physical"
        ))
        updated_state = manager.update_game(state)
        logger.info(f"✅ Updated game phase to: {updated_state.phase}")
        
        # Clean up
        manager.delete_game(state.game_id)
        logger.info("✅ Deleted test game")
        
        logger.info("🎉 State manager test complete!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        raise


if __name__ == "__main__":
    test_state_manager()