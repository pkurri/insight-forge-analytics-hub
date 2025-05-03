# Conversation Memory System (Modular)

## Overview
This module provides a modular, extensible system for managing AI chat conversation memory, evaluations, user preferences, and continuous learning. It is fully decoupled into persistence, analytics, advanced operations, and search/filter utilities.

### Key Components
- `conversation_memory.py`: Main coordination class, manages in-memory structures and delegates to submodules.
- `conversation_store.py`: Handles all persistence (load/save/export/import).
- `conversation_ops.py`: Advanced operations (merge, split, archive, purge, validate, log summary).
- `conversation_search.py`: Search and filter utilities.

### Usage
- Use the `ConversationMemory` singleton for all business logic and high-level operations.
- All persistence and advanced operations are delegated to submodules.

### Example
```python
from services.conversation_memory import conversation_memory

# Create a new conversation
cid = conversation_memory.create_conversation(user_id="user123")

# Add a message
conversation_memory.add_message(cid, {"role": "user", "content": "Hello!"})

# Search messages
results = conversation_memory.search_messages("Hello")

# Export memory
conversation_memory.export_memory("/tmp/memory_export.json")
```

### Testing
- See `tests/test_conversation_memory.py` for unit and integration tests.
- All modules are tested independently and in integration.

### Analytics & Anomaly Detection
- The system supports analytics on conversations, evaluations, and user feedback.
- Anomaly detection is triggered automatically when loading the same dataset repeatedly (see below for details).

---

## Anomaly Detection on Dataset Load
When the same dataset is loaded multiple times, the system:
- Tracks loading frequency and metadata.
- Runs anomaly detection to flag suspicious patterns (e.g., repeated loads, inconsistent metadata, or feedback spikes).
- Raises alerts or logs anomalies for further investigation.

---

## Extending
- Add new analytics or anomaly detection logic in `conversation_ops.py` or a new analytics module.
- Extend business logic in `conversation_memory.py` as needed.

---

## Maintainers
- All persistence, search, and advanced operations should be delegated to submodules.
- Keep `conversation_memory.py` as a thin coordinator.
