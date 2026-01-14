"""Task status enumeration and validation."""

from enum import Enum


class TaskStatus(str, Enum):
    """Task status enumeration."""
    
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    RETRYING = "RETRYING"
    TIMEOUT = "TIMEOUT"


# Valid status transitions
STATUS_TRANSITIONS = {
    TaskStatus.PENDING: [TaskStatus.QUEUED, TaskStatus.CANCELLED],
    TaskStatus.QUEUED: [TaskStatus.RUNNING, TaskStatus.CANCELLED],
    TaskStatus.RUNNING: [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.TIMEOUT, TaskStatus.CANCELLED],
    TaskStatus.FAILED: [TaskStatus.RETRYING, TaskStatus.CANCELLED],
    TaskStatus.RETRYING: [TaskStatus.QUEUED, TaskStatus.CANCELLED],
    TaskStatus.COMPLETED: [],  # Terminal state
    TaskStatus.CANCELLED: [],  # Terminal state
    TaskStatus.TIMEOUT: [TaskStatus.RETRYING, TaskStatus.CANCELLED],
}


def is_valid_transition(current: str, new: str) -> bool:
    """Check if status transition is valid.
    
    Args:
        current: Current status
        new: New status to transition to
        
    Returns:
        True if transition is valid, False otherwise
    """
    try:
        current_status = TaskStatus(current)
        new_status = TaskStatus(new)
        return new_status in STATUS_TRANSITIONS.get(current_status, [])
    except (ValueError, KeyError):
        return False


def is_terminal_status(status: str) -> bool:
    """Check if status is terminal (no further transitions).
    
    Args:
        status: Status to check
        
    Returns:
        True if terminal status, False otherwise
    """
    try:
        status_enum = TaskStatus(status)
        return len(STATUS_TRANSITIONS.get(status_enum, [])) == 0
    except ValueError:
        return False


def get_valid_next_statuses(current: str) -> list[str]:
    """Get list of valid next statuses.
    
    Args:
        current: Current status
        
    Returns:
        List of valid next status values
    """
    try:
        current_status = TaskStatus(current)
        return [s.value for s in STATUS_TRANSITIONS.get(current_status, [])]
    except ValueError:
        return []
