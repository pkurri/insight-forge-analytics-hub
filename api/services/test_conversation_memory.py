import pytest
from services.conversation_memory import conversation_memory, ConversationMemory
import uuid

def test_create_and_get_conversation():
    cid = conversation_memory.create_conversation(user_id="test_user")
    convo = conversation_memory.get_conversation(cid)
    assert convo is not None
    assert convo['user_id'] == "test_user"
    assert convo['messages'] == []

def test_add_message():
    cid = conversation_memory.create_conversation(user_id="test_user")
    msg = {"role": "user", "content": "Hi there!"}
    assert conversation_memory.add_message(cid, msg)
    convo = conversation_memory.get_conversation(cid)
    assert len(convo['messages']) == 1
    assert convo['messages'][0]['content'] == "Hi there!"

def test_export_and_import_memory(tmp_path):
    cid = conversation_memory.create_conversation(user_id="test_user")
    export_path = tmp_path / "memory_export.json"
    assert conversation_memory.export_memory(str(export_path))
    # Simulate clearing and re-importing
    conversation_memory.conversations = {}
    assert conversation_memory.import_memory(str(export_path))
    assert conversation_memory.get_conversation(cid) is not None

def test_anomaly_detection_on_dataset_load():
    mem = ConversationMemory()
    dataset_id = "dataset_XYZ"
    mem.dataset_loads = {}
    for _ in range(5):
        mem.track_dataset_load(dataset_id, user_id="u1")
    # Should raise anomaly after threshold
    assert mem.detect_anomaly_on_load(dataset_id)
