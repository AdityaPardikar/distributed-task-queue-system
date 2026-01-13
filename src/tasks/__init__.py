"""Task registry for task function definitions"""

from typing import Callable, Dict

# Global task registry
_task_registry: Dict[str, Callable] = {}


def register_task(name: str, func: Callable):
    """Register a task function"""
    _task_registry[name] = func


def get_task_function(name: str) -> Callable:
    """Get task function by name"""
    return _task_registry.get(name)


def list_registered_tasks():
    """List all registered tasks"""
    return list(_task_registry.keys())


# Example task functions
def send_email(email: str, subject: str, body: str) -> dict:
    """Example email sending task"""
    # This will be replaced with actual SMTP logic in Week 5
    return {
        "status": "sent",
        "email": email,
        "subject": subject,
    }


def process_data(data: dict) -> dict:
    """Example data processing task"""
    return {
        "status": "processed",
        "items_count": len(data),
    }


# Register default tasks
register_task("send_email", send_email)
register_task("process_data", process_data)
