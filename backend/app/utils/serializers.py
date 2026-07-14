"""JSON serialization utilities."""

from datetime import datetime
from typing import Any, Dict
import json


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects."""
    
    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def serialize_game_state(game_state: Any) -> Dict[str, Any]:
    """Serialize game state to dict with datetime conversion."""
    if not game_state:
        return None
    
    try:
        # Use model_dump with datetime conversion
        data = game_state.model_dump()
        
        # Convert datetime objects to ISO format strings
        if "created_at" in data and isinstance(data["created_at"], datetime):
            data["created_at"] = data["created_at"].isoformat()
        
        return data
    except Exception as e:
        # Fallback to manual serialization
        return {
            "error": f"Serialization error: {str(e)}"
        }


def to_json(data: Any) -> str:
    """Convert any data to JSON string with datetime support."""
    return json.dumps(data, cls=DateTimeEncoder)