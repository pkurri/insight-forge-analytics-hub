import os
import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from .conversation_store import ConversationStore
from .conversation_ops import (
    merge_conversations, split_conversation, archive_conversation, purge_old_conversations,
    validate_memory_integrity, log_memory_summary
)
from .conversation_search import search_messages, filter_conversations_by_time
from .analytics.anomaly_detection import AnomalyDetector
from .analytics.analytics_dashboard import AnalyticsDashboard
from .analytics.feedback_analytics import FeedbackAnalytics
from .analytics.time_series_analytics import TimeSeriesAnalytics

logger = logging.getLogger(__name__)

class ConversationMemory:
    """
    Modular Conversation Memory System for AI chat history, evaluations, and continuous learning.

    - All persistence (load/save/export/import) is handled by ConversationStore.
    - All advanced operations (merge, split, archive, purge, validate, log) are handled by ConversationOps.
    - All search/filter is handled by ConversationSearch.
    - This class only manages in-memory structure, business logic, and delegates to submodules.
    - See wrapper methods for usage patterns and extension points.
    """
    # Usage: see create_conversation, add_message, add_evaluation for business logic;
    #        see merge_conversations, search_messages, export_memory, etc. for delegation to submodules.
    
    def __init__(self):
        """
        Initialize the conversation memory system
        """
        self.memory_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'conversation_memory')
        self.store = ConversationStore(self.memory_path)
        self.conversations = {}
        self.user_preferences = {}
        self.learning_patterns = {}
        self.dataset_loads = {}  # {dataset_id: [timestamps]}
        self.anomaly_log = []    # List of anomaly events
        self.anomaly_detector = AnomalyDetector()
        self.dashboard = AnalyticsDashboard()
        self.feedback_analytics = FeedbackAnalytics()
        self._load_memory()
        self.time_series_analytics = TimeSeriesAnalytics()

    
    def _load_memory(self):
        """
        Load conversation memory from disk using ConversationStore
        """
        data = self.store.load()
        self.conversations = data.get('conversations', {})
        self.user_preferences = data.get('user_preferences', {})
        self.learning_patterns = data.get('learning_patterns', {})
    
    def _save_memory(self):
        """
        Save conversation memory to disk using ConversationStore
        """
        data = {
            'conversations': self.conversations,
            'user_preferences': self.user_preferences,
            'learning_patterns': self.learning_patterns
        }
        return self.store.save(data)

    
    def create_conversation(self, user_id: str = None) -> str:
        """
        Create a new conversation and return its ID
        
        Args:
            user_id: Optional user ID to associate with the conversation
            
        Returns:
            Conversation ID
        """
        conversation_id = str(uuid.uuid4())
        
        self.conversations[conversation_id] = {
            'id': conversation_id,
            'user_id': user_id,
            'messages': [],
            'evaluations': [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'metadata': {}
        }
        
        # Save memory
        self._save_memory()
        
        return conversation_id
    
    def add_message(self, conversation_id: str, message: Dict[str, Any]) -> bool:
        """
        Add a message to a conversation
        
        Args:
            conversation_id: ID of the conversation
            message: Message to add, with format:
                {
                    'role': 'user' or 'assistant',
                    'content': 'Message content',
                    'timestamp': ISO timestamp (optional),
                    'metadata': Additional metadata (optional)
                }
                
        Returns:
            True if successful, False otherwise
        """
        if conversation_id not in self.conversations:
            return False
        
        # Add timestamp if not provided
        if 'timestamp' not in message:
            message['timestamp'] = datetime.now().isoformat()
        
        # Add message ID if not provided
        if 'id' not in message:
            message['id'] = str(uuid.uuid4())
        
        # Add message to conversation
        self.conversations[conversation_id]['messages'].append(message)
        self.conversations[conversation_id]['updated_at'] = datetime.now().isoformat()
        
        # Save memory (periodically)
        if len(self.conversations[conversation_id]['messages']) % 5 == 0:
            self._save_memory()
        
        return True
    
    def add_evaluation(self, conversation_id: str, message_id: str, evaluation: Dict[str, Any]) -> bool:
        """
        Add an evaluation for a message in a conversation
        
        Args:
            conversation_id: ID of the conversation
            message_id: ID of the message being evaluated
            evaluation: Evaluation data
                
        Returns:
            True if successful, False otherwise
        """
        if conversation_id not in self.conversations:
            return False
        
        # Add timestamp if not provided
        if 'timestamp' not in evaluation:
            evaluation['timestamp'] = datetime.now().isoformat()
        
        # Add evaluation ID if not provided
        if 'id' not in evaluation:
            evaluation['id'] = str(uuid.uuid4())
        
        # Add message ID to evaluation
        evaluation['message_id'] = message_id
        
        # Add evaluation to conversation
        self.conversations[conversation_id]['evaluations'].append(evaluation)
        
        # Process evaluation for learning
        self._process_evaluation_for_learning(conversation_id, message_id, evaluation)
        
        # Save memory
        self._save_memory()
        
        return True
    
    def _process_evaluation_for_learning(self, conversation_id: str, message_id: str, evaluation: Dict[str, Any]):
        """
        Process an evaluation to extract learning patterns
        
        Args:
            conversation_id: ID of the conversation
            message_id: ID of the message being evaluated
            evaluation: Evaluation data
        """
        # Find the message
        message = None
        for msg in self.conversations[conversation_id]['messages']:
            if msg.get('id') == message_id:
                message = msg
                break
        
        if not message or message.get('role') != 'assistant':
            return
        
        # Extract scores
        scores = evaluation.get('scores', {})
        if not scores:
            return
        
        # Extract learning patterns based on scores
        for metric, score in scores.items():
            if metric not in self.learning_patterns:
                self.learning_patterns[metric] = {
                    'high_scoring_examples': [],
                    'low_scoring_examples': []
                }
            
            # Define score thresholds
            if score >= 85:  # High score
                # Add to high scoring examples (limited to 20 examples)
                if len(self.learning_patterns[metric]['high_scoring_examples']) >= 20:
                    self.learning_patterns[metric]['high_scoring_examples'].pop(0)
                
                self.learning_patterns[metric]['high_scoring_examples'].append({
                    'query': self._find_query_for_response(conversation_id, message_id),
                    'response': message.get('content', ''),
                    'score': score,
                    'evaluation': evaluation.get('explanation', '')
                })
            
            elif score <= 60:  # Low score
                # Add to low scoring examples (limited to 20 examples)
                if len(self.learning_patterns[metric]['low_scoring_examples']) >= 20:
                    self.learning_patterns[metric]['low_scoring_examples'].pop(0)
                
                self.learning_patterns[metric]['low_scoring_examples'].append({
                    'query': self._find_query_for_response(conversation_id, message_id),
                    'response': message.get('content', ''),
                    'score': score,
                    'evaluation': evaluation.get('explanation', '')
                })
    
    def _find_query_for_response(self, conversation_id: str, message_id: str) -> str:
        """
        Find the user query that prompted a specific response
        
        Args:
            conversation_id: ID of the conversation
            message_id: ID of the assistant's message
            
        Returns:
            User query or empty string if not found
        """
        messages = self.conversations[conversation_id]['messages']
        assistant_index = None
        
        # Find the assistant message
        for i, msg in enumerate(messages):
            if msg.get('id') == message_id:
                assistant_index = i
                break
        
        if assistant_index is None or assistant_index == 0:
            return ""
        
        # Find the most recent user message before the assistant message
        for i in range(assistant_index - 1, -1, -1):
            if messages[i].get('role') == 'user':
                return messages[i].get('content', '')
        
        return ""
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a conversation by ID
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Conversation data or None if not found
        """
        return self.conversations.get(conversation_id)
    
    def get_learning_context(self, query: str, metrics: List[str] = None) -> Dict[str, Any]:
        """
        Get learning context based on previous evaluations
        
        Args:
            query: User query to get context for
            metrics: List of metrics to prioritize (e.g., 'accuracy', 'helpfulness')
            
        Returns:
            Learning context with examples and guidance
        """
        if not metrics:
            metrics = list(self.learning_patterns.keys())
        
        # Get relevant examples for each metric
        examples = {
            'positive_examples': [],
            'negative_examples': []
        }
        
        for metric in metrics:
            if metric in self.learning_patterns:
                # Add high scoring examples
                for example in self.learning_patterns[metric]['high_scoring_examples'][-3:]:
                    examples['positive_examples'].append({
                        'metric': metric,
                        'query': example.get('query', ''),
                        'response': example.get('response', ''),
                        'score': example.get('score', 0),
                        'feedback': example.get('evaluation', '')
                    })
                
                # Add low scoring examples
                for example in self.learning_patterns[metric]['low_scoring_examples'][-3:]:
                    examples['negative_examples'].append({
                        'metric': metric,
                        'query': example.get('query', ''),
                        'response': example.get('response', ''),
                        'score': example.get('score', 0),
                        'feedback': example.get('evaluation', '')
                    })
        
        # Generate guidance based on examples
        guidance = self._generate_guidance(examples, query)
        
        return {
            'examples': examples,
            'guidance': guidance
        }
    
    def _generate_guidance(self, examples: Dict[str, List[Dict[str, Any]]], query: str) -> str:
        """
        Generate guidance for improving responses based on learning patterns
        
        Args:
            examples: Positive and negative examples
            query: Current user query
            
        Returns:
            Guidance string for improving responses
        """
        guidance = """Based on previous evaluations, please ensure your response:
"""
        
        # Add guidance from positive examples
        if examples['positive_examples']:
            guidance += "\n- DO:"
            positive_patterns = set()
            
            for example in examples['positive_examples']:
                feedback = example.get('feedback', '')
                if feedback:
                    # Extract key positive points (simple heuristic)
                    for line in feedback.split('\n'):
                        if 'good' in line.lower() or 'excellent' in line.lower() or 'strength' in line.lower():
                            positive_patterns.add(line.strip())
            
            for pattern in list(positive_patterns)[:5]:  # Limit to 5 patterns
                guidance += f"\n  - {pattern}"
        
        # Add guidance from negative examples
        if examples['negative_examples']:
            guidance += "\n- DON'T:"
            negative_patterns = set()
            
            for example in examples['negative_examples']:
                feedback = example.get('feedback', '')
                if feedback:
                    # Extract key negative points (simple heuristic)
                    for line in feedback.split('\n'):
                        if 'poor' in line.lower() or 'issue' in line.lower() or 'lacking' in line.lower() or 'improve' in line.lower():
                            negative_patterns.add(line.strip())
            
            for pattern in list(negative_patterns)[:5]:  # Limit to 5 patterns
                guidance += f"\n  - {pattern}"
        
        return guidance
    
    def update_user_preference(self, user_id: str, preference: Dict[str, Any]) -> bool:
        """
        Update or add a user preference
        
        Args:
            user_id: ID of the user
            preference: Preference data with format:
                {
                    'key': 'preference_key',
                    'value': 'preference_value',
                    'metadata': Additional metadata (optional)
                }
                
        Returns:
            True if successful, False otherwise
        """
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}
        
        key = preference.get('key')
        if not key:
            return False
        
        # Update preference
        self.user_preferences[user_id][key] = {
            'value': preference.get('value'),
            'metadata': preference.get('metadata', {}),
            'updated_at': datetime.now().isoformat()
        }
        
        # Save memory
        self._save_memory()
        
        return True
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get all preferences for a user
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary of user preferences
        """
        return self.user_preferences.get(user_id, {})
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent conversations
        
        Args:
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversations, most recent first
        """
        # Convert to list and sort by updated_at
        conversations = list(self.conversations.values())
        conversations.sort(key=lambda c: c.get('updated_at', ''), reverse=True)
        
        # Return limited number of conversations with limited data
        result = []
        for convo in conversations[:limit]:
            result.append({
                'id': convo.get('id'),
                'user_id': convo.get('user_id'),
                'message_count': len(convo.get('messages', [])),
                'evaluation_count': len(convo.get('evaluations', [])),
                'created_at': convo.get('created_at'),
                'updated_at': convo.get('updated_at')
            })
        
        return result

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation by its ID.
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            self._save_memory()
            return True
        return False

    def clear_conversations(self) -> None:
        """
        Remove all conversations from memory.
        """
        self.conversations = {}
        self._save_memory()

    def export_memory(self, export_path: str = None) -> bool:
        """
        Export the entire memory to a JSON file.
        """
        if not export_path:
            export_path = os.path.join(self.memory_path, f"memory_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        try:
            data = {
                'conversations': self.conversations,
                'user_preferences': self.user_preferences,
                'learning_patterns': self.learning_patterns
            }
            with open(export_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Exported conversation memory to {export_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting memory: {str(e)}")
            return False

    def import_memory(self, import_path: str) -> bool:
        """
        Import memory from a JSON file.
        """
        try:
            with open(import_path, 'r') as f:
                data = json.load(f)
                self.conversations = data.get('conversations', {})
                self.user_preferences = data.get('user_preferences', {})
                self.learning_patterns = data.get('learning_patterns', {})
            self._save_memory()
            logger.info(f"Imported conversation memory from {import_path}")
            return True
        except Exception as e:
            logger.error(f"Error importing memory: {str(e)}")
            return False

    def get_conversation_ids(self) -> list:
        """
        Get all conversation IDs.
        """
        return list(self.conversations.keys())

    def get_conversations_by_user(self, user_id: str) -> list:
        """
        Get all conversations for a specific user.
        """
        return [c for c in self.conversations.values() if c.get('user_id') == user_id]

    def get_conversation_count(self) -> int:
        """
        Return the total number of conversations.
        """
        return len(self.conversations)

    def get_message_count(self) -> int:
        """
        Return the total number of messages across all conversations.
        """
        return sum(len(c.get('messages', [])) for c in self.conversations.values())

    def get_evaluation_count(self) -> int:
        """
        Return the total number of evaluations across all conversations.
        """
        return sum(len(c.get('evaluations', [])) for c in self.conversations.values())

    def reset_learning_patterns(self) -> None:
        """
        Clear all learned patterns.
        """
        self.learning_patterns = {}
        self._save_memory()

    def delete_message(self, conversation_id: str, message_id: str) -> bool:
        """
        Delete a message from a conversation by message ID.
        """
        convo = self.conversations.get(conversation_id)
        if not convo:
            return False
        messages = convo.get('messages', [])
        new_messages = [m for m in messages if m.get('id') != message_id]
        if len(new_messages) == len(messages):
            return False  # Not found
        convo['messages'] = new_messages
        self._save_memory()
        return True

    def update_message(self, conversation_id: str, message_id: str, new_message_data: dict) -> bool:
        """
        Update a message's content or metadata in a conversation.
        """
        convo = self.conversations.get(conversation_id)
        if not convo:
            return False
        for idx, m in enumerate(convo.get('messages', [])):
            if m.get('id') == message_id:
                convo['messages'][idx].update(new_message_data)
                self._save_memory()
                return True
        return False

    def find_message(self, message_id: str) -> Optional[dict]:
        """
        Find and return a message by ID across all conversations.
        """
        for convo in self.conversations.values():
            for m in convo.get('messages', []):
                if m.get('id') == message_id:
                    return m
        return None

    def delete_evaluation(self, conversation_id: str, evaluation_id: str) -> bool:
        """
        Delete an evaluation from a conversation by evaluation ID.
        """
        convo = self.conversations.get(conversation_id)
        if not convo:
            return False
        evaluations = convo.get('evaluations', [])
        new_evals = [e for e in evaluations if e.get('id') != evaluation_id]
        if len(new_evals) == len(evaluations):
            return False
        convo['evaluations'] = new_evals
        self._save_memory()
        return True

    def update_evaluation(self, conversation_id: str, evaluation_id: str, new_evaluation_data: dict) -> bool:
        """
        Update an evaluation's content or metadata in a conversation.
        """
        convo = self.conversations.get(conversation_id)
        if not convo:
            return False
        for idx, e in enumerate(convo.get('evaluations', [])):
            if e.get('id') == evaluation_id:
                convo['evaluations'][idx].update(new_evaluation_data)
                self._save_memory()
                return True
        return False

    def find_evaluation(self, evaluation_id: str) -> Optional[dict]:
        """
        Find and return an evaluation by ID across all conversations.
        """
        for convo in self.conversations.values():
            for e in convo.get('evaluations', []):
                if e.get('id') == evaluation_id:
                    return e
        return None

    def get_conversation_summary(self, conversation_id: str) -> dict:
        """
        Return a summary of a conversation (first/last message, counts, user, etc.)
        """
        convo = self.conversations.get(conversation_id)
        if not convo:
            return {}
        messages = convo.get('messages', [])
        evaluations = convo.get('evaluations', [])
        return {
            'id': convo.get('id'),
            'user_id': convo.get('user_id'),
            'created_at': convo.get('created_at'),
            'updated_at': convo.get('updated_at'),
            'message_count': len(messages),
            'evaluation_count': len(evaluations),
            'first_message': messages[0] if messages else None,
            'last_message': messages[-1] if messages else None
        }

    def get_memory_stats(self) -> dict:
        """
        Return statistics about the memory (counts, users, etc.)
        """
        user_ids = set(c.get('user_id') for c in self.conversations.values() if c.get('user_id'))
        return {
            'conversation_count': len(self.conversations),
            'message_count': self.get_message_count(),
            'evaluation_count': self.get_evaluation_count(),
            'user_count': len(user_ids)
        }

    def anonymize_conversations(self) -> None:
        """
        Remove/mask user IDs and sensitive fields for privacy.
        """
        for convo in self.conversations.values():
            convo['user_id'] = None
            for msg in convo.get('messages', []):
                msg.pop('user_id', None)
            for eval in convo.get('evaluations', []):
                eval.pop('user_id', None)
        self._save_memory()

    def merge_conversations(self, conversation_ids: list, new_conversation_id: str = None) -> dict:
        """
        Merge multiple conversations by IDs into one.
        """
        convos = [self.conversations[cid] for cid in conversation_ids if cid in self.conversations]
        merged = merge_conversations(convos, new_conversation_id)
        return merged

    def split_conversation(self, conversation_id: str, split_index: int) -> list:
        """
        Split a conversation into two at a given message index.
        """
        convo = self.conversations.get(conversation_id)
        if not convo:
            return []
        return split_conversation(convo, split_index)

    def archive_conversation(self, conversation_id: str, archive_path: str) -> bool:
        """
        Archive a conversation to a file and remove from active memory.
        """
        convo = self.conversations.get(conversation_id)
        if not convo:
            return False
        success = archive_conversation(convo, archive_path)
        if success:
            del self.conversations[conversation_id]
            self._save_memory()
        return success

    def purge_old_conversations(self, before_date: str) -> int:
        """
        Delete conversations not updated since a given ISO date.
        Returns the number of conversations deleted.
        """
        orig_count = len(self.conversations)
        self.conversations = purge_old_conversations(self.conversations, before_date)
        self._save_memory()
        return orig_count - len(self.conversations)

    def validate_memory_integrity(self) -> bool:
        """
        Check for orphaned messages/evaluations or structural inconsistencies.
        """
        return validate_memory_integrity(self.conversations)

    def search_messages(self, query: str, role: str = None, user_id: str = None):
        """
        Search all messages for a keyword, optionally filtering by role or user.
        """
        return search_messages(list(self.conversations.values()), query, role, user_id)

    def filter_conversations_by_time(self, start: str, end: str):
        """
        Return conversations active within a specific time window (ISO format).
        """
        return filter_conversations_by_time(list(self.conversations.values()), start, end)

    def export_memory(self, export_path: str = None) -> bool:
        """
        Export the entire memory to a JSON file using ConversationStore.
        """
        data = {
            'conversations': self.conversations,
            'user_preferences': self.user_preferences,
            'learning_patterns': self.learning_patterns
        }
        return self.store.export(data, export_path)

    def import_memory(self, import_path: str) -> bool:
        """
        Import memory from a JSON file using ConversationStore.
        """
        data = self.store.import_(import_path)
        self.conversations = data.get('conversations', {})
        self.user_preferences = data.get('user_preferences', {})
        self.learning_patterns = data.get('learning_patterns', {})
        self._save_memory()
        return True

    def track_dataset_load(self, dataset_id: str, user_id: str = None):
        """
        Track when a dataset is loaded. Used for anomaly detection analytics.
        """
        ts = datetime.now().isoformat()
        if dataset_id not in self.dataset_loads:
            self.dataset_loads[dataset_id] = []
        self.dataset_loads[dataset_id].append({"timestamp": ts, "user_id": user_id})
        # Advanced anomaly detection
        loads = self.dataset_loads[dataset_id]
        repeated = self.anomaly_detector.detect_repeated_loads(loads)
        # Statistical anomaly (e.g., loads per hour)
        counts = [len(self.dataset_loads[dataset_id])]  # Placeholder: extend for time-bucketed counts
        statistical = self.anomaly_detector.detect_statistical_anomaly(counts)
        if repeated or statistical:
            self.anomaly_log.append({
                "event": "anomaly_detected",
                "dataset_id": dataset_id,
                "timestamp": ts,
                "user_id": user_id,
                "reason": "Repeated or statistical anomaly in dataset load"
            })

    def show_dashboard(self):
        """
        Show analytics dashboard with message volume, user activity, and anomalies.
        """
        self.dashboard.plot_message_volume(self.conversations)
        self.dashboard.plot_user_activity(self.conversations)
        self.dashboard.plot_anomalies(self.anomaly_log)

    def get_memory_stats(self) -> dict:
        """
        Return analytics summary: counts of conversations, messages, evaluations, users, datasets loaded, anomalies.
        """
        num_convs = len(self.conversations)
        num_msgs = sum(len(c['messages']) for c in self.conversations.values())
        num_evals = sum(len(c['evaluations']) for c in self.conversations.values())
        users = set(c['user_id'] for c in self.conversations.values() if c.get('user_id'))
        datasets = list(self.dataset_loads.keys())
        return {
            "conversations": num_convs,
            "messages": num_msgs,
            "evaluations": num_evals,
            "users": len(users),
            "datasets_loaded": len(datasets),
            "anomalies": len(self.anomaly_log)
        }

    def get_anomaly_report(self) -> list:
        """
        Return a list of anomaly events detected during dataset loads.
        """
        return self.anomaly_log

    def get_feedback_summary(self) -> dict:
        """
        Get summary statistics for all feedback/evaluations in memory.
        """
        all_evals = [e for c in self.conversations.values() for e in c.get('evaluations', [])]
        return self.feedback_analytics.feedback_summary(all_evals)

    def get_most_common_feedback(self, n=3) -> list:
        """
        Get the n most common feedback strings from all evaluations.
        """
        all_evals = [e for c in self.conversations.values() for e in c.get('evaluations', [])]
        return self.feedback_analytics.most_common_feedback(all_evals, n=n)

    def get_message_volume_over_time(self, freq='D') -> dict:
        """
        Get message volume over time (by day or hour).
        """
        return self.time_series_analytics.message_volume_over_time(self.conversations, freq)

    def plot_message_volume_over_time(self, freq='D'):
        """
        Plot message volume over time (by day or hour).
        """
        self.time_series_analytics.plot_message_volume_over_time(self.conversations, freq)

# Create singleton instance
conversation_memory = ConversationMemory()
