import os
import json
import pickle
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ConversationStore:
    """
    Handles persistence and retrieval of conversations and related data.
    """
    def __init__(self, memory_path: str):
        self.memory_path = memory_path
        os.makedirs(self.memory_path, exist_ok=True)
        self.memory_file = os.path.join(self.memory_path, 'memory.pkl')

    def load(self) -> Dict[str, Any]:
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'rb') as f:
                    data = pickle.load(f)
                    logger.info(f"Loaded conversation memory with {len(data.get('conversations', {}))} conversations")
                    return data
            except Exception as e:
                logger.error(f"Error loading conversation memory: {str(e)}")
        return {'conversations': {}, 'user_preferences': {}, 'learning_patterns': {}}

    def save(self, data: Dict[str, Any]) -> bool:
        try:
            with open(self.memory_file, 'wb') as f:
                pickle.dump(data, f)
            logger.info("Saved conversation memory")
            return True
        except Exception as e:
            logger.error(f"Error saving conversation memory: {str(e)}")
            return False

    def export(self, data: Dict[str, Any], export_path: str = None) -> bool:
        if not export_path:
            export_path = os.path.join(self.memory_path, f"memory_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        try:
            with open(export_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Exported conversation memory to {export_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting memory: {str(e)}")
            return False

    def import_(self, import_path: str) -> Dict[str, Any]:
        try:
            with open(import_path, 'r') as f:
                data = json.load(f)
            logger.info(f"Imported conversation memory from {import_path}")
            return data
        except Exception as e:
            logger.error(f"Error importing memory: {str(e)}")
            return {'conversations': {}, 'user_preferences': {}, 'learning_patterns': {}}
