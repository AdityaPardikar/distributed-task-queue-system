"""Core broker for Redis operations"""

from typing import Any, Optional

from src.cache.client import RedisClient, get_redis_client
from src.cache.keys import CacheKeys


class TaskBroker:
    """Redis broker for task queue operations"""

    def __init__(self, redis_client: RedisClient = None):
        """Initialize task broker"""
        self.redis = redis_client or get_redis_client()

    # Task queue operations
    def enqueue_task(self, task_id: str, priority: str = "MEDIUM") -> bool:
        """Add task to queue"""
        key = CacheKeys.task_queue(priority)
        return self.redis.rpush(key, task_id) > 0

    def dequeue_task(self, priority: str = "MEDIUM", timeout: int = 5) -> Optional[str]:
        """Get next task from queue"""
        key = CacheKeys.task_queue(priority)
        result = self.redis.blpop(key, timeout)
        return result[1] if result else None

    def get_task_meta(self, task_id: str) -> dict:
        """Get task metadata"""
        key = CacheKeys.task_meta(task_id)
        return self.redis.hgetall(key)

    def set_task_meta(self, task_id: str, metadata: dict) -> bool:
        """Set task metadata"""
        key = CacheKeys.task_meta(task_id)
        return self.redis.hset(key, metadata) > 0

    def update_task_meta(self, task_id: str, field: str, value: Any) -> bool:
        """Update task metadata field"""
        key = CacheKeys.task_meta(task_id)
        return self.redis.hset(key, {field: value}) > 0

    def delete_task_meta(self, task_id: str) -> bool:
        """Delete task metadata"""
        key = CacheKeys.task_meta(task_id)
        return self.redis.delete(key) > 0

    # Worker operations
    def register_worker(self, worker_id: str, metadata: dict) -> bool:
        """Register worker"""
        worker_key = CacheKeys.worker(worker_id)
        registry_key = CacheKeys.worker_registry()

        # Add to registry
        self.redis.sadd(registry_key, worker_id)

        # Store worker info
        return self.redis.hset(worker_key, metadata) > 0

    def unregister_worker(self, worker_id: str) -> bool:
        """Unregister worker"""
        worker_key = CacheKeys.worker(worker_id)
        registry_key = CacheKeys.worker_registry()

        # Remove from registry
        self.redis.srem(registry_key, worker_id)

        # Delete worker info
        return self.redis.delete(worker_key) > 0

    def get_worker_info(self, worker_id: str) -> dict:
        """Get worker information"""
        key = CacheKeys.worker(worker_id)
        return self.redis.hgetall(key)

    def update_worker_heartbeat(self, worker_id: str, timestamp: int) -> bool:
        """Update worker heartbeat"""
        key = CacheKeys.worker(worker_id)
        return self.redis.hset(key, {"last_heartbeat": str(timestamp)}) > 0

    def get_active_workers(self) -> set:
        """Get all active workers"""
        key = CacheKeys.worker_registry()
        return self.redis.smembers(key)

    # Scheduled tasks
    def schedule_task(self, task_id: str, scheduled_time: int) -> bool:
        """Add task to scheduled queue"""
        key = CacheKeys.scheduled_tasks()
        return self.redis.zadd(key, {task_id: scheduled_time}) > 0

    def get_due_tasks(self, current_time: int) -> list:
        """Get tasks due for execution"""
        key = CacheKeys.scheduled_tasks()
        return self.redis.zrangebyscore(key, 0, current_time)

    def remove_scheduled_task(self, task_id: str) -> bool:
        """Remove task from scheduled queue"""
        key = CacheKeys.scheduled_tasks()
        return self.redis.zrem(key, task_id) > 0

    # Rate limiting
    def check_rate_limit(self, resource: str, identifier: str, limit: int, window: int) -> bool:
        """Check if rate limit exceeded"""
        key = CacheKeys.rate_limit(resource, identifier)
        count = self.redis.get(key)

        if count is None:
            self.redis.set(key, "1", ttl=window)
            return True

        count = int(count)
        if count >= limit:
            return False

        self.redis.incr(key)
        return True

    # Campaign progress
    def update_campaign_progress(self, campaign_id: str, progress: dict) -> bool:
        """Update campaign progress"""
        key = CacheKeys.campaign_progress(campaign_id)
        return self.redis.hset(key, progress) > 0

    def get_campaign_progress(self, campaign_id: str) -> dict:
        """Get campaign progress"""
        key = CacheKeys.campaign_progress(campaign_id)
        return self.redis.hgetall(key)

    # Task dependencies
    def add_task_dependency(self, parent_id: str, child_id: str) -> bool:
        """Add task dependency"""
        key = CacheKeys.task_dependencies(parent_id)
        return self.redis.sadd(key, child_id) > 0

    def get_task_dependencies(self, parent_id: str) -> set:
        """Get task dependencies"""
        key = CacheKeys.task_dependencies(parent_id)
        return self.redis.smembers(key)

    def remove_task_dependency(self, parent_id: str, child_id: str) -> bool:
        """Remove task dependency"""
        key = CacheKeys.task_dependencies(parent_id)
        return self.redis.srem(key, child_id) > 0

    # Task completion events
    def publish_task_completion(self, task_id: str, status: str) -> bool:
        """Publish task completion event"""
        channel = "task:completed"
        message = f"{task_id}:{status}"
        return self.redis.publish(channel, message) > 0

    def close(self):
        """Close broker connection"""
        self.redis.close()


# Global broker instance
_broker = None


def get_broker() -> TaskBroker:
    """Get or create task broker"""
    global _broker
    if _broker is None:
        _broker = TaskBroker()
    return _broker
