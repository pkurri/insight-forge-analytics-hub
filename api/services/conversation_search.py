import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def search_messages(conversations: List[Dict[str, Any]], query: str, role: Optional[str] = None, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Search all messages for a keyword, optionally filtering by role or user.
    """
    results = []
    for convo in conversations:
        for msg in convo.get('messages', []):
            if query.lower() in msg.get('content', '').lower():
                if (role is None or msg.get('role') == role) and (user_id is None or msg.get('user_id') == user_id):
                    results.append(msg)
    return results

def filter_conversations_by_time(conversations: List[Dict[str, Any]], start: str, end: str) -> List[Dict[str, Any]]:
    """
    Return conversations active within a specific time window (ISO format).
    """
    from datetime import datetime
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)
    filtered = []
    for c in conversations:
        updated_at = c.get('updated_at')
        if updated_at:
            updated_dt = datetime.fromisoformat(updated_at)
            if start_dt <= updated_dt <= end_dt:
                filtered.append(c)
    return filtered
