"""Development and testing utilities"""

import json
from typing import Any, Dict


def serialize_task_args(args: list, kwargs: dict) -> tuple:
    """Serialize task arguments to JSON-compatible format"""
    try:
        json.dumps(args)
        json.dumps(kwargs)
        return args, kwargs
    except (TypeError, ValueError) as e:
        raise ValueError(f"Task arguments must be JSON serializable: {e}")


def deserialize_task_args(args: list, kwargs: dict) -> tuple:
    """Deserialize task arguments from storage"""
    return args, kwargs


def format_task_for_queue(task_id: str, task_data: Dict[str, Any]) -> str:
    """Format task data for queue storage"""
    return str(task_id)


def parse_queued_task(task_id: str) -> str:
    """Parse task ID from queued task"""
    return task_id


class TaskExecutionError(Exception):
    """Raised when task execution fails"""
    pass


class TaskTimeoutError(TaskExecutionError):
    """Raised when task execution times out"""
    pass


class TaskSerializationError(Exception):
    """Raised when task arguments cannot be serialized"""
    pass
