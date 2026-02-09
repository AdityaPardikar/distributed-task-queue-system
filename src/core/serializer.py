"""Task serialization module for handling complex Python objects."""

import base64
import json
import pickle
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID


class SerializationFormat(str, Enum):
    """Supported serialization formats."""
    JSON = "json"
    PICKLE = "pickle"


class TaskSerializer:
    """Handles serialization and deserialization of task payloads."""

    def __init__(self, format: SerializationFormat = SerializationFormat.JSON):
        """Initialize serializer with specified format.
        
        Args:
            format: Serialization format to use (JSON or PICKLE)
        """
        self.format = format

    def serialize(self, data: Any) -> bytes:
        """Serialize data to bytes.
        
        Args:
            data: Data to serialize
            
        Returns:
            Serialized data as bytes
            
        Raises:
            ValueError: If serialization fails
        """
        try:
            if self.format == SerializationFormat.JSON:
                return self._serialize_json(data)
            elif self.format == SerializationFormat.PICKLE:
                return self._serialize_pickle(data)
            else:
                raise ValueError(f"Unsupported format: {self.format}")
        except Exception as e:
            raise ValueError(f"Serialization failed: {str(e)}") from e

    def deserialize(self, data: bytes) -> Any:
        """Deserialize bytes to Python object.
        
        Args:
            data: Serialized data as bytes
            
        Returns:
            Deserialized Python object
            
        Raises:
            ValueError: If deserialization fails
        """
        try:
            if self.format == SerializationFormat.JSON:
                return self._deserialize_json(data)
            elif self.format == SerializationFormat.PICKLE:
                return self._deserialize_pickle(data)
            else:
                raise ValueError(f"Unsupported format: {self.format}")
        except Exception as e:
            raise ValueError(f"Deserialization failed: {str(e)}") from e

    def _serialize_json(self, data: Any) -> bytes:
        """Serialize data to JSON bytes with custom encoder.
        
        Args:
            data: Data to serialize
            
        Returns:
            JSON bytes
        """
        json_str = json.dumps(data, cls=CustomJSONEncoder, ensure_ascii=False)
        return json_str.encode('utf-8')

    def _deserialize_json(self, data: bytes) -> Any:
        """Deserialize JSON bytes to Python object.
        
        Args:
            data: JSON bytes
            
        Returns:
            Python object
        """
        json_str = data.decode('utf-8')
        return json.loads(json_str, object_hook=custom_json_decoder)

    def _serialize_pickle(self, data: Any) -> bytes:
        """Serialize data using pickle.
        
        Args:
            data: Data to serialize
            
        Returns:
            Pickled bytes
        """
        return pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)

    def _deserialize_pickle(self, data: bytes) -> Any:
        """Deserialize pickle bytes to Python object.
        
        Args:
            data: Pickled bytes
            
        Returns:
            Python object
        """
        return pickle.loads(data)


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for handling special Python types."""

    def default(self, obj: Any) -> Any:
        """Convert special types to JSON-serializable format.
        
        Args:
            obj: Object to encode
            
        Returns:
            JSON-serializable representation
        """
        if isinstance(obj, datetime):
            return {
                "__type__": "datetime",
                "value": obj.isoformat()
            }
        elif isinstance(obj, UUID):
            return {
                "__type__": "uuid",
                "value": str(obj)
            }
        elif isinstance(obj, Enum):
            return {
                "__type__": "enum",
                "class": f"{obj.__class__.__module__}.{obj.__class__.__name__}",
                "value": obj.value
            }
        elif isinstance(obj, bytes):
            return {
                "__type__": "bytes",
                "value": base64.b64encode(obj).decode('ascii')
            }
        elif hasattr(obj, '__dict__'):
            # Handle custom objects with __dict__
            return {
                "__type__": "object",
                "class": f"{obj.__class__.__module__}.{obj.__class__.__name__}",
                "data": obj.__dict__
            }
        return super().default(obj)


def custom_json_decoder(dct: Dict[str, Any]) -> Any:
    """Custom JSON decoder for reconstructing special Python types.
    
    Args:
        dct: Dictionary from JSON
        
    Returns:
        Reconstructed Python object or original dict
    """
    if "__type__" not in dct:
        return dct

    obj_type = dct["__type__"]
    
    if obj_type == "datetime":
        return datetime.fromisoformat(dct["value"])
    elif obj_type == "uuid":
        return UUID(dct["value"])
    elif obj_type == "bytes":
        return base64.b64decode(dct["value"].encode('ascii'))
    elif obj_type == "enum":
        # Note: Enum reconstruction requires importing the class
        # For now, just return the value
        return dct["value"]
    elif obj_type == "object":
        # Return as dict for custom objects
        return dct.get("data", {})
    
    return dct


def get_serializer(format: Optional[str] = None) -> TaskSerializer:
    """Factory function to get a serializer instance.
    
    Args:
        format: Serialization format ('json' or 'pickle'). Defaults to 'json'.
        
    Returns:
        TaskSerializer instance
    """
    if format is None:
        format = SerializationFormat.JSON
    elif isinstance(format, str):
        format = SerializationFormat(format.lower())
    
    return TaskSerializer(format=format)
