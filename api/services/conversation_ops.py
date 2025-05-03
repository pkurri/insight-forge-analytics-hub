import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

def merge_conversations(conversations: List[Dict[str, Any]], new_conversation_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Merge multiple conversations into one, combining messages and evaluations chronologically.
    """
    if not conversations:
        return {}
    merged = {
        'id': new_conversation_id or conversations[0]['id'],
        'user_id': conversations[0].get('user_id'),
        'messages': [],
        'evaluations': [],
        'created_at': min(c.get('created_at', datetime.now().isoformat()) for c in conversations),
        'updated_at': max(c.get('updated_at', datetime.now().isoformat()) for c in conversations),
        'metadata': {}
    }
    all_messages = []
    all_evals = []
    for c in conversations:
        all_messages.extend(c.get('messages', []))
        all_evals.extend(c.get('evaluations', []))
    merged['messages'] = sorted(all_messages, key=lambda m: m.get('timestamp', ''))
    merged['evaluations'] = sorted(all_evals, key=lambda e: e.get('timestamp', ''))
    return merged

def split_conversation(conversation: Dict[str, Any], split_index: int) -> List[Dict[str, Any]]:
    """
    Split a conversation into two at a given message index.
    """
    messages = conversation.get('messages', [])
    evals = conversation.get('evaluations', [])
    conv1 = conversation.copy()
    conv2 = conversation.copy()
    conv1['messages'] = messages[:split_index]
    conv2['messages'] = messages[split_index:]
    # Assign evaluations based on message_id
    msg_ids1 = set(m.get('id') for m in conv1['messages'])
    msg_ids2 = set(m.get('id') for m in conv2['messages'])
    conv1['evaluations'] = [e for e in evals if e.get('message_id') in msg_ids1]
    conv2['evaluations'] = [e for e in evals if e.get('message_id') in msg_ids2]
    conv1['id'] = f"{conversation['id']}_1"
    conv2['id'] = f"{conversation['id']}_2"
    return [conv1, conv2]

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

def archive_conversation(conversation: Dict[str, Any], archive_path: str) -> bool:
    """
    Move a conversation to an archive file and remove it from active memory.
    """
    try:
        with open(archive_path, 'w') as f:
            json.dump(conversation, f, indent=2, default=str)
        logger.info(f"Archived conversation to {archive_path}")
        return True
    except Exception as e:
        logger.error(f"Error archiving conversation: {str(e)}")
        return False

def purge_old_conversations(conversations: Dict[str, Any], before_date: str) -> Dict[str, Any]:
    """
    Delete conversations not updated since a given ISO date.
    """
    cutoff = datetime.fromisoformat(before_date)
    to_delete = [cid for cid, c in conversations.items() if c.get('updated_at') and datetime.fromisoformat(c['updated_at']) < cutoff]
    for cid in to_delete:
        del conversations[cid]
    logger.info(f"Purged {len(to_delete)} old conversations before {before_date}")
    return conversations

def validate_memory_integrity(conversations: Dict[str, Any]) -> bool:
    """
    Check for orphaned messages/evaluations or structural inconsistencies.
    """
    for cid, convo in conversations.items():
        msg_ids = set(m.get('id') for m in convo.get('messages', []))
        for eval in convo.get('evaluations', []):
            if eval.get('message_id') and eval['message_id'] not in msg_ids:
                logger.warning(f"Orphaned evaluation in conversation {cid}: {eval}")
                return False
    return True

def log_memory_summary(conversations: Dict[str, Any]):
    """
    Log a summary of memory stats for quick inspection.
    """
    logger.info(f"Total conversations: {len(conversations)}")
    msg_count = sum(len(c.get('messages', [])) for c in conversations.values())
    eval_count = sum(len(c.get('evaluations', [])) for c in conversations.values())
    logger.info(f"Total messages: {msg_count}, Total evaluations: {eval_count}")
