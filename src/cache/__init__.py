"""Redis cache key patterns"""

from src.config.constants import (
    CAMPAIGN_PROGRESS_PREFIX,
    QUEUE_PREFIX,
    RATE_LIMIT_PREFIX,
    SCHEDULED_TASKS_KEY,
    TASK_COMPLETED_STREAM,
    TASK_DEPENDENCIES_PREFIX,
    TASK_META_PREFIX,
    WORKER_PREFIX,
    WORKER_REGISTRY_KEY,
)


class CacheKeys:
    """Cache key patterns for Redis"""

    # Task queue keys
    @staticmethod
    def task_queue(priority: str) -> str:
        """Get task queue key by priority"""
        return f"{QUEUE_PREFIX}:{priority}"

    # Task metadata
    @staticmethod
    def task_meta(task_id: str) -> str:
        """Get task metadata key"""
        return f"{TASK_META_PREFIX}:{task_id}"

    # Worker keys
    @staticmethod
    def worker(worker_id: str) -> str:
        """Get worker key"""
        return f"{WORKER_PREFIX}:{worker_id}"

    @staticmethod
    def worker_registry() -> str:
        """Get worker registry key"""
        return WORKER_REGISTRY_KEY

    # Scheduled tasks
    @staticmethod
    def scheduled_tasks() -> str:
        """Get scheduled tasks key"""
        return SCHEDULED_TASKS_KEY

    # Rate limiting
    @staticmethod
    def rate_limit(resource: str, identifier: str) -> str:
        """Get rate limit key"""
        return f"{RATE_LIMIT_PREFIX}:{resource}:{identifier}"

    # Campaign progress
    @staticmethod
    def campaign_progress(campaign_id: str) -> str:
        """Get campaign progress key"""
        return f"{CAMPAIGN_PROGRESS_PREFIX}:{campaign_id}:progress"

    # Task dependencies
    @staticmethod
    def task_dependencies(task_id: str) -> str:
        """Get task dependencies key"""
        return f"{TASK_DEPENDENCIES_PREFIX}:{task_id}"

    # Task completion stream
    @staticmethod
    def task_completed_stream() -> str:
        """Get task completion stream key"""
        return TASK_COMPLETED_STREAM
