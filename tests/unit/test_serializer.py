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
        
        # Bytes are converted to string
        assert isinstance(deserialized["binary"], str)

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
        
        class CustomClass:
            def __init__(self, value):
                self.value = value
            
            def __eq__(self, other):
                return isinstance(other, CustomClass) and self.value == other.value
        
        obj = CustomClass(42)
        data = {"object": obj}
        
        serialized = serializer.serialize(data)
        deserialized = serializer.deserialize(serialized)
        
        assert deserialized["object"] == obj
        assert deserialized["object"].value == 42

    def test_serialization_error_handling(self):
        """Test error handling for invalid serialization."""
        serializer = TaskSerializer(format=SerializationFormat.JSON)
        
        # Create non-serializable object
        class NonSerializable:
            def __repr__(self):
                raise Exception("Cannot serialize")
        
        # Should raise ValueError
        with pytest.raises(ValueError, match="Serialization failed"):
            serializer.serialize({"obj": NonSerializable()})

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
