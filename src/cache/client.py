"""Cache and Redis integration"""

import json
from typing import Any, Optional

import redis
from src.config import get_settings

settings = get_settings()


class RedisClient:
    """Redis client wrapper for task queue operations"""

    def __init__(self, url: str = None):
        """Initialize Redis client"""
        self.url = url or settings.REDIS_URL
        self.client = redis.from_url(
            self.url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True,
            health_check_interval=30,
        )

    def ping(self) -> bool:
        """Check Redis connection"""
        try:
            return self.client.ping()
        except Exception as e:
            print(f"Redis connection error: {e}")
            return False

    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set key-value pair"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            if ttl:
                return self.client.setex(key, ttl, value)
            return self.client.set(key, value)
        except Exception as e:
            print(f"Redis set error: {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        try:
            value = self.client.get(key)
            if value and (value.startswith("{") or value.startswith("[")):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return value
        except Exception as e:
            print(f"Redis get error: {e}")
            return None

    def delete(self, *keys: str) -> int:
        """Delete keys"""
        try:
            return self.client.delete(*keys)
        except Exception as e:
            print(f"Redis delete error: {e}")
            return 0

    def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False

    # Queue operations
    def lpush(self, key: str, *values) -> int:
        """Push values to queue (left)"""
        try:
            return self.client.lpush(key, *values)
        except Exception as e:
            print(f"Redis lpush error: {e}")
            return 0

    def rpush(self, key: str, *values) -> int:
        """Push values to queue (right)"""
        try:
            return self.client.rpush(key, *values)
        except Exception as e:
            print(f"Redis rpush error: {e}")
            return 0

    def blpop(self, key: str, timeout: int = 5) -> Optional[tuple]:
        """Pop value from queue (blocking left)"""
        try:
            return self.client.blpop(key, timeout=timeout)
        except Exception as e:
            print(f"Redis blpop error: {e}")
            return None

    def brpop(self, key: str, timeout: int = 5) -> Optional[tuple]:
        """Pop value from queue (blocking right)"""
        try:
            return self.client.brpop(key, timeout=timeout)
        except Exception as e:
            print(f"Redis brpop error: {e}")
            return None

    # Hash operations
    def hset(self, key: str, mapping: dict) -> int:
        """Set hash fields"""
        try:
            return self.client.hset(key, mapping=mapping)
        except Exception as e:
            print(f"Redis hset error: {e}")
            return 0

    def hget(self, key: str, field: str) -> Optional[str]:
        """Get hash field value"""
        try:
            return self.client.hget(key, field)
        except Exception as e:
            print(f"Redis hget error: {e}")
            return None

    def hgetall(self, key: str) -> dict:
        """Get all hash fields"""
        try:
            return self.client.hgetall(key)
        except Exception as e:
            print(f"Redis hgetall error: {e}")
            return {}

    # Set operations
    def sadd(self, key: str, *members) -> int:
        """Add members to set"""
        try:
            return self.client.sadd(key, *members)
        except Exception as e:
            print(f"Redis sadd error: {e}")
            return 0

    def srem(self, key: str, *members) -> int:
        """Remove members from set"""
        try:
            return self.client.srem(key, *members)
        except Exception as e:
            print(f"Redis srem error: {e}")
            return 0

    def smembers(self, key: str) -> set:
        """Get all set members"""
        try:
            return self.client.smembers(key)
        except Exception as e:
            print(f"Redis smembers error: {e}")
            return set()

    # Sorted set operations
    def zadd(self, key: str, mapping: dict) -> int:
        """Add members to sorted set"""
        try:
            return self.client.zadd(key, mapping)
        except Exception as e:
            print(f"Redis zadd error: {e}")
            return 0

    def zrange(self, key: str, start: int = 0, end: int = -1) -> list:
        """Get range from sorted set"""
        try:
            return self.client.zrange(key, start, end)
        except Exception as e:
            print(f"Redis zrange error: {e}")
            return []

    def zrangebyscore(self, key: str, min: float, max: float) -> list:
        """Get sorted set members by score range"""
        try:
            return self.client.zrangebyscore(key, min, max)
        except Exception as e:
            print(f"Redis zrangebyscore error: {e}")
            return []

    def zrem(self, key: str, *members) -> int:
        """Remove members from sorted set"""
        try:
            return self.client.zrem(key, *members)
        except Exception as e:
            print(f"Redis zrem error: {e}")
            return 0

    # Pub/Sub operations
    def publish(self, channel: str, message: str) -> int:
        """Publish message to channel"""
        try:
            return self.client.publish(channel, message)
        except Exception as e:
            print(f"Redis publish error: {e}")
            return 0

    def subscribe(self, *channels):
        """Subscribe to channels"""
        try:
            return self.client.pubsub().subscribe(*channels)
        except Exception as e:
            print(f"Redis subscribe error: {e}")
            return None

    def incr(self, key: str) -> int:
        """Increment counter"""
        try:
            return self.client.incr(key)
        except Exception as e:
            print(f"Redis incr error: {e}")
            return 0

    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on key"""
        try:
            return self.client.expire(key, seconds)
        except Exception as e:
            print(f"Redis expire error: {e}")
            return False

    def ttl(self, key: str) -> int:
        """Get remaining TTL in seconds"""
        try:
            return self.client.ttl(key)
        except Exception as e:
            print(f"Redis ttl error: {e}")
            return -1

    def close(self):
        """Close Redis connection"""
        try:
            self.client.close()
        except Exception as e:
            print(f"Redis close error: {e}")


# Global Redis client instance
_redis_client = None


def get_redis_client() -> RedisClient:
    """Get or create Redis client"""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client
