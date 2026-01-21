"""Core broker for Redis operations"""

import json
from typing import Any, Dict, Optional, List

from src.cache.client import RedisClient, get_redis_client
from src.cache.keys import CacheKeys
from src.core.serializer import get_serializer


class TaskBroker:
    """Redis broker for task queue operations"""

    def __init__(self, redis_client: RedisClient = None):
        """Initialize task broker"""
        self.redis = redis_client or get_redis_client()
        self.serializer = get_serializer("json")

    # Task queue operations with priority
    def enqueue_task(
        self, 
        task_id: str, 
        priority: int = 5,
        task_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add task to priority-based queue.
        
        Args:
            task_id: Unique task identifier
            priority: Priority level (1-10, where 10 is highest)
            task_data: Optional task metadata to store
            
        Returns:
            True if task was enqueued successfully
        """
        # Validate priority
        if not 1 <= priority <= 10:
            priority = 5  # Default to medium priority
        
        # Determine queue based on priority
        if priority >= 8:
            queue = "HIGH"
        elif priority >= 4:
            queue = "MEDIUM"
        else:
            queue = "LOW"
        
        key = CacheKeys.task_queue(queue)
        
        # Store task metadata if provided
        if task_data:
            self.set_task_metadata(task_id, task_data)
        
        # Add to queue
        return self.redis.rpush(key, task_id) > 0

    def dequeue_task(
        self, 
        priorities: Optional[List[str]] = None,
        timeout: int = 5
    ) -> Optional[str]:
        """Get next task from queue, checking high priority first.
        
        Args:
            priorities: List of priorities to check (default: ["HIGH", "MEDIUM", "LOW"])
            timeout: Blocking timeout in seconds
            
        Returns:
            Task ID or None if no tasks available
        """
        if priorities is None:
            priorities = ["HIGH", "MEDIUM", "LOW"]
        
        # Try each priority queue in order
        for priority in priorities:
            key = CacheKeys.task_queue(priority)
            result = self.redis.blpop(key, timeout=1)  # Short timeout for each queue
            if result:
                return result[1]
        
        return None

    def get_task_metadata(self, task_id: str) -> Dict[str, Any]:
        """Get task metadata from Redis.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task metadata dictionary
        """
        key = CacheKeys.task_meta(task_id)
        data = self.redis.hgetall(key)
        
        # Deserialize JSON fields if needed
        if data and "payload" in data:
            try:
                data["payload"] = json.loads(data["payload"])
            except (json.JSONDecodeError, TypeError):
                pass
        
        return data

    def set_task_metadata(self, task_id: str, metadata: Dict[str, Any]) -> bool:
        """Set task metadata in Redis.
        
        Args:
            task_id: Task identifier
            metadata: Dictionary of metadata to store
            
        Returns:
            True if metadata was set successfully
        """
        key = CacheKeys.task_meta(task_id)
        
        # Serialize complex fields
        processed_metadata = {}
        for k, v in metadata.items():
            if isinstance(v, (dict, list)):
                processed_metadata[k] = json.dumps(v)
            else:
                processed_metadata[k] = str(v)
        
        return self.redis.hset(key, processed_metadata) > 0

    def update_task_status(self, task_id: str, status: str, **extra_fields) -> bool:
        """Update task status and optional extra fields.
        
        Args:
            task_id: Task identifier
            status: New status value
            **extra_fields: Additional fields to update
            
        Returns:
            True if status was updated successfully
        """
        key = CacheKeys.task_meta(task_id)
        update_data = {"status": status}
        update_data.update(extra_fields)
        
        # Convert values to strings
        processed_data = {k: str(v) for k, v in update_data.items()}
        
        return self.redis.hset(key, processed_data) > 0

    def get_task_meta(self, task_id: str) -> dict:
        """Get task metadata (alias for backward compatibility)"""
        return self.get_task_metadata(task_id)

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

    # Dead letter queue operations
    def move_to_dlq(self, task_id: str, failure_reason: str, task_data: Optional[Dict[str, Any]] = None) -> bool:
        """Move a task to the dead letter queue.

        Args:
            task_id: Task identifier
            failure_reason: Reason for failure
            task_data: Optional metadata to persist

        Returns:
            True if task added to DLQ successfully
        """
        timestamp = int(self.redis.time()[0]) if hasattr(self.redis, "time") else 0
        zset_key = CacheKeys.dlq_zset()
        meta_key = CacheKeys.dlq_meta(task_id)

        payload = {"failure_reason": failure_reason, "task_id": task_id, "timestamp": str(timestamp)}
        if task_data:
            payload.update(task_data)

        # Store metadata in hash
        self.redis.hset(meta_key, {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in payload.items()})

        # Add to sorted set for ordering
        added = self.redis.zadd(zset_key, {task_id: timestamp})
        return added > 0

    def list_dlq(self, start: int = 0, stop: int = -1) -> List[Dict[str, Any]]:
        """List DLQ tasks with metadata."""
        zset_key = CacheKeys.dlq_zset()
        task_ids = self.redis.zrange(zset_key, start, stop)

        items = []
        for tid in task_ids:
            meta_key = CacheKeys.dlq_meta(tid)
            meta = self.redis.hgetall(meta_key)
            if meta:
                # Deserialize JSON fields
                if "task_data" in meta:
                    try:
                        meta["task_data"] = json.loads(meta["task_data"])
                    except (TypeError, json.JSONDecodeError):
                        pass
                items.append({"task_id": tid, **meta})
        return items

    def remove_from_dlq(self, task_id: str) -> bool:
        """Remove a task from DLQ (both zset and metadata)."""
        zset_key = CacheKeys.dlq_zset()
        meta_key = CacheKeys.dlq_meta(task_id)
        self.redis.delete(meta_key)
        removed = self.redis.zrem(zset_key, task_id)
        return removed > 0

    def get_dlq_meta(self, task_id: str) -> Dict[str, Any]:
        """Get DLQ metadata for a task."""
        meta_key = CacheKeys.dlq_meta(task_id)
        meta = self.redis.hgetall(meta_key)
        if meta and "task_data" in meta:
            try:
                meta["task_data"] = json.loads(meta["task_data"])
            except (TypeError, json.JSONDecodeError):
                pass
        return meta

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
