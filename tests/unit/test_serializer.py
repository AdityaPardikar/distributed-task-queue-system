"""Unit tests for task serialization."""

import json
import pickle
from datetime import datetime
from uuid import uuid4

import pytest

from src.core.serializer import (
    TaskSerializer,
    SerializationFormat,
    get_serializer,
    CustomJSONEncoder,
    custom_json_decoder,
)


class TestTaskSerializer:
    """Test TaskSerializer class."""

    def test_json_serialization_basic_types(self):
        """Test JSON serialization of basic Python types."""
        serializer = TaskSerializer(format=SerializationFormat.JSON)
        
        data = {
            "string": "hello",
            "integer": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
            "list": [1, 2, 3],
            "nested": {"key": "value"}
        }
        
        serialized = serializer.serialize(data)
        assert isinstance(serialized, bytes)
        
        deserialized = serializer.deserialize(serialized)
        assert deserialized == data

    def test_json_serialization_datetime(self):
        """Test JSON serialization of datetime objects."""
        serializer = TaskSerializer(format=SerializationFormat.JSON)
        
        now = datetime.utcnow()
        data = {"timestamp": now}
        
        serialized = serializer.serialize(data)
        deserialized = serializer.deserialize(serialized)
        
        # DateTime should be preserved (ISO format)
        assert isinstance(deserialized["timestamp"], datetime)
        assert deserialized["timestamp"].isoformat() == now.isoformat()

    def test_json_serialization_uuid(self):
        """Test JSON serialization of UUID objects."""
        serializer = TaskSerializer(format=SerializationFormat.JSON)
        
        task_id = uuid4()
        data = {"id": task_id}
        
        serialized = serializer.serialize(data)
        deserialized = serializer.deserialize(serialized)
        
        # UUID should be preserved
        assert str(deserialized["id"]) == str(task_id)

    def test_json_serialization_bytes(self):
        """Test JSON serialization of bytes."""
        serializer = TaskSerializer(format=SerializationFormat.JSON)
        
        data = {"binary": b"hello world"}
        
        serialized = serializer.serialize(data)
        deserialized = serializer.deserialize(serialized)
        
        # Bytes are correctly preserved (base64 encoded/decoded)
        assert isinstance(deserialized["binary"], bytes)
        assert deserialized["binary"] == b"hello world"

    def test_pickle_serialization_basic(self):
        """Test pickle serialization of basic types."""
        serializer = TaskSerializer(format=SerializationFormat.PICKLE)
        
        data = {"key": "value", "number": 123, "list": [1, 2, 3]}
        
        serialized = serializer.serialize(data)
        assert isinstance(serialized, bytes)
        
        deserialized = serializer.deserialize(serialized)
        assert deserialized == data

    def test_pickle_serialization_complex_objects(self):
        """Test pickle serialization of complex Python objects."""
        serializer = TaskSerializer(format=SerializationFormat.PICKLE)
        
        # Use module-level class (datetime) or built-in types
        from datetime import datetime
        
        obj = datetime(2024, 1, 1, 12, 0, 0)
        data = {"datetime": obj, "nested": {"list": [1, 2, 3], "dict": {"key": "value"}}}
        
        serialized = serializer.serialize(data)
        deserialized = serializer.deserialize(serialized)
        
        assert deserialized["datetime"] == obj
        assert deserialized["nested"]["list"] == [1, 2, 3]

    def test_serialization_error_handling(self):
        """Test error handling for invalid serialization."""
        serializer = TaskSerializer(format=SerializationFormat.JSON)
        
        # Create object that will fail JSON serialization
        # Sets are not JSON serializable
        with pytest.raises(ValueError, match="Serialization failed"):
            serializer.serialize({"obj": {1, 2, 3}})

    def test_deserialization_error_handling(self):
        """Test error handling for invalid deserialization."""
        serializer = TaskSerializer(format=SerializationFormat.JSON)
        
        # Invalid JSON bytes
        with pytest.raises(ValueError, match="Deserialization failed"):
            serializer.deserialize(b"invalid json {")

    def test_get_serializer_factory(self):
        """Test get_serializer factory function."""
        # Default format (JSON)
        serializer = get_serializer()
        assert serializer.format == SerializationFormat.JSON
        
        # Explicit JSON
        serializer = get_serializer("json")
        assert serializer.format == SerializationFormat.JSON
        
        # Pickle format
        serializer = get_serializer("pickle")
        assert serializer.format == SerializationFormat.PICKLE

    def test_complex_nested_data(self):
        """Test serialization of complex nested data structures."""
        serializer = TaskSerializer(format=SerializationFormat.JSON)
        
        data = {
            "user": {
                "id": uuid4(),
                "created_at": datetime.utcnow(),
                "profile": {
                    "name": "John Doe",
                    "tags": ["tag1", "tag2"],
                    "metadata": {
                        "score": 95.5,
                        "active": True
                    }
                }
            },
            "tasks": [
                {"name": "task1", "priority": 10},
                {"name": "task2", "priority": 5}
            ]
        }
        
        serialized = serializer.serialize(data)
        deserialized = serializer.deserialize(serialized)
        
        # Verify structure is preserved
        assert "user" in deserialized
        assert "profile" in deserialized["user"]
        assert len(deserialized["tasks"]) == 2
        assert deserialized["tasks"][0]["name"] == "task1"
