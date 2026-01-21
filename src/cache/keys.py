"""Cache key helpers for Redis operations."""

class CacheKeys:
    """Static helpers to generate Redis cache keys."""

    @staticmethod
    def task_queue(priority: str) -> str:
        return f"queue:{priority.lower()}"

    @staticmethod
    def task_meta(task_id: str) -> str:
        return f"task:{task_id}:meta"

    @staticmethod
    def worker(worker_id: str) -> str:
        return f"worker:{worker_id}"

    @staticmethod
    def worker_registry() -> str:
        return "workers:registry"

    @staticmethod
    def scheduled_tasks() -> str:
        return "tasks:scheduled"

    @staticmethod
    def rate_limit(resource: str, identifier: str) -> str:
        return f"ratelimit:{resource}:{identifier}"

    @staticmethod
    def campaign_progress(campaign_id: str) -> str:
        return f"campaign:{campaign_id}:progress"

    @staticmethod
    def task_dependencies(parent_id: str) -> str:
        return f"task:{parent_id}:dependencies"

    @staticmethod
    def dlq_zset() -> str:
        return "tasks:dlq"

    @staticmethod
    def dlq_meta(task_id: str) -> str:
        return f"task:{task_id}:dlq"
