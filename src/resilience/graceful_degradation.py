"""Graceful degradation strategies."""

from enum import Enum
from typing import Any, Callable, Optional, Dict, List

from src.cache.client import RedisClient, get_redis_client


class DegradationStrategy(str, Enum):
    """Degradation strategy options."""
    QUEUE_TO_FALLBACK = "queue_to_fallback"      # Queue to fallback queue
    RETURN_CACHED = "return_cached"              # Return cached result
    DEFAULT_VALUE = "default_value"              # Return default value
    SKIP_ENRICHMENT = "skip_enrichment"          # Skip non-critical enrichment
    REDUCE_THROUGHPUT = "reduce_throughput"      # Reduce task submission rate
    ASYNC_FALLBACK = "async_fallback"            # Process asynchronously


class GracefulDegradation:
    """Handle graceful degradation when services degrade."""

    def __init__(self, redis_client: Optional[RedisClient] = None):
        """Initialize graceful degradation handler.
        
        Args:
            redis_client: Redis client for state tracking
        """
        self.redis = redis_client or get_redis_client()
        self.key_degraded_services = "degraded:services"
        self.key_throughput_limit = "degraded:throughput_limit"
        self.key_cache_prefix = "degraded:cache"

    def mark_service_degraded(
        self,
        service_name: str,
        strategy: DegradationStrategy,
        duration_seconds: int = 300,
        metadata: Optional[Dict] = None,
    ) -> bool:
        """Mark a service as degraded.
        
        Args:
            service_name: Name of degraded service
            strategy: Degradation strategy to apply
            duration_seconds: How long to apply degradation
            metadata: Additional metadata
            
        Returns:
            True if marked successfully
        """
        degradation_info = {
            "service": service_name,
            "strategy": strategy.value,
            "marked_at": str(__import__('datetime').datetime.utcnow().isoformat()),
            "metadata": metadata or {},
        }

        self.redis.hset(
            self.key_degraded_services,
            service_name,
            __import__('json').dumps(degradation_info),
            ttl=duration_seconds,
        )

        return True

    def is_service_degraded(self, service_name: str) -> bool:
        """Check if service is degraded.
        
        Args:
            service_name: Service name
            
        Returns:
            True if degraded
        """
        return self.redis.hexists(self.key_degraded_services, service_name)

    def get_degradation_strategy(
        self,
        service_name: str,
    ) -> Optional[DegradationStrategy]:
        """Get degradation strategy for a service.
        
        Args:
            service_name: Service name
            
        Returns:
            Degradation strategy or None
        """
        info = self.redis.hget(self.key_degraded_services, service_name)
        if not info:
            return None

        import json
        data = json.loads(info)
        return DegradationStrategy(data["strategy"])

    def set_throughput_limit(
        self,
        tasks_per_minute: int,
        duration_seconds: int = 300,
    ) -> bool:
        """Set reduced throughput limit during degradation.
        
        Args:
            tasks_per_minute: Max tasks per minute
            duration_seconds: Duration of limit
            
        Returns:
            True if set successfully
        """
        self.redis.set(
            self.key_throughput_limit,
            str(tasks_per_minute),
            ttl=duration_seconds,
        )
        return True

    def get_throughput_limit(self) -> Optional[int]:
        """Get current throughput limit.
        
        Returns:
            Tasks per minute limit or None
        """
        limit = self.redis.get(self.key_throughput_limit)
        return int(limit) if limit else None

    def cache_result(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = 3600,
    ) -> bool:
        """Cache a result for fallback.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Cache TTL
            
        Returns:
            True if cached
        """
        import json
        cache_key = f"{self.key_cache_prefix}:{key}"
        self.redis.set(cache_key, json.dumps(value), ttl=ttl_seconds)
        return True

    def get_cached_result(self, key: str) -> Optional[Any]:
        """Retrieve cached result.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        import json
        cache_key = f"{self.key_cache_prefix}:{key}"
        value = self.redis.get(cache_key)
        return json.loads(value) if value else None

    def clear_degradation(self, service_name: str) -> bool:
        """Clear degradation state for a service.
        
        Args:
            service_name: Service name
            
        Returns:
            True if cleared
        """
        self.redis.hdel(self.key_degraded_services, service_name)
        return True

    def get_all_degraded_services(self) -> Dict[str, Dict]:
        """Get all currently degraded services.
        
        Returns:
            Dictionary of degraded services
        """
        import json
        services = self.redis.hgetall(self.key_degraded_services)
        
        if not services:
            return {}

        return {
            name: json.loads(info) 
            for name, info in services.items()
        }


# Global instance
_degradation: Optional[GracefulDegradation] = None


def get_graceful_degradation() -> GracefulDegradation:
    """Get global graceful degradation instance."""
    global _degradation
    if _degradation is None:
        _degradation = GracefulDegradation()
    return _degradation
