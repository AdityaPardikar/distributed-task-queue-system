"""Chaos engineering utilities for testing resilience."""

import asyncio
import random
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar

from src.cache.client import get_redis_client
from src.config import get_settings

settings = get_settings()

T = TypeVar('T')


class ChaosType(str, Enum):
    """Types of chaos that can be injected."""
    LATENCY = "latency"
    ERROR = "error"
    TIMEOUT = "timeout"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    NETWORK_PARTITION = "network_partition"


class ChaosConfig:
    """Configuration for chaos injection."""
    
    def __init__(
        self,
        chaos_type: ChaosType,
        probability: float = 0.1,
        min_latency_ms: int = 100,
        max_latency_ms: int = 5000,
        error_rate: float = 0.1,
        error_message: str = "Chaos induced error",
        enabled: bool = True,
    ):
        self.chaos_type = chaos_type
        self.probability = min(1.0, max(0.0, probability))
        self.min_latency_ms = min_latency_ms
        self.max_latency_ms = max_latency_ms
        self.error_rate = error_rate
        self.error_message = error_message
        self.enabled = enabled


class ChaosEngineering:
    """Chaos engineering utilities for testing system resilience."""
    
    def __init__(self):
        self.redis = get_redis_client()
        self.key_prefix = "chaos"
        self.active_experiments: Dict[str, ChaosConfig] = {}
    
    def start_experiment(
        self,
        name: str,
        config: ChaosConfig,
        duration_seconds: int = 300,
    ) -> Dict[str, Any]:
        """Start a chaos experiment.
        
        Args:
            name: Experiment name
            config: Chaos configuration
            duration_seconds: Duration of experiment
            
        Returns:
            Experiment info
        """
        experiment_key = f"{self.key_prefix}:experiment:{name}"
        experiment_data = {
            "name": name,
            "chaos_type": config.chaos_type.value,
            "probability": config.probability,
            "enabled": config.enabled,
            "started_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(seconds=duration_seconds)).isoformat(),
        }
        
        self.redis.hset(experiment_key, mapping=experiment_data)
        self.redis.expire(experiment_key, duration_seconds)
        self.active_experiments[name] = config
        
        return experiment_data
    
    def stop_experiment(self, name: str) -> bool:
        """Stop a chaos experiment.
        
        Args:
            name: Experiment name
            
        Returns:
            True if stopped
        """
        experiment_key = f"{self.key_prefix}:experiment:{name}"
        self.redis.delete(experiment_key)
        
        if name in self.active_experiments:
            del self.active_experiments[name]
        
        return True
    
    def is_experiment_active(self, name: str) -> bool:
        """Check if an experiment is active.
        
        Args:
            name: Experiment name
            
        Returns:
            True if active
        """
        experiment_key = f"{self.key_prefix}:experiment:{name}"
        return self.redis.exists(experiment_key)
    
    def get_active_experiments(self) -> List[Dict[str, Any]]:
        """Get all active experiments.
        
        Returns:
            List of experiment info
        """
        pattern = f"{self.key_prefix}:experiment:*"
        experiments = []
        
        for key in self.redis.keys(pattern):
            data = self.redis.hgetall(key)
            if data:
                experiments.append(data)
        
        return experiments
    
    def inject_latency(
        self,
        min_ms: int = 100,
        max_ms: int = 5000,
        probability: float = 1.0,
    ) -> None:
        """Inject artificial latency.
        
        Args:
            min_ms: Minimum latency in milliseconds
            max_ms: Maximum latency in milliseconds
            probability: Probability of injection
        """
        if random.random() < probability:
            delay_ms = random.randint(min_ms, max_ms)
            asyncio.get_event_loop().run_until_complete(
                asyncio.sleep(delay_ms / 1000)
            )
    
    def inject_error(
        self,
        error_class: type = Exception,
        message: str = "Chaos induced error",
        probability: float = 1.0,
    ) -> None:
        """Inject an error.
        
        Args:
            error_class: Exception class to raise
            message: Error message
            probability: Probability of injection
        """
        if random.random() < probability:
            raise error_class(message)
    
    def should_fail(self, probability: float = 0.1) -> bool:
        """Determine if an operation should fail.
        
        Args:
            probability: Failure probability
            
        Returns:
            True if should fail
        """
        return random.random() < probability


def chaos_monkey(
    chaos_type: ChaosType = ChaosType.LATENCY,
    probability: float = 0.1,
    **kwargs
) -> Callable:
    """Decorator to inject chaos into a function.
    
    Args:
        chaos_type: Type of chaos to inject
        probability: Probability of chaos injection
        **kwargs: Additional chaos config
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **func_kwargs) -> T:
            if settings.APP_ENV == "production":
                # Don't inject chaos in production
                return await func(*args, **func_kwargs)
            
            if random.random() < probability:
                chaos = ChaosEngineering()
                
                if chaos_type == ChaosType.LATENCY:
                    min_ms = kwargs.get("min_latency_ms", 100)
                    max_ms = kwargs.get("max_latency_ms", 5000)
                    await asyncio.sleep(random.randint(min_ms, max_ms) / 1000)
                
                elif chaos_type == ChaosType.ERROR:
                    error_msg = kwargs.get("error_message", "Chaos induced error")
                    raise Exception(error_msg)
                
                elif chaos_type == ChaosType.TIMEOUT:
                    timeout = kwargs.get("timeout_seconds", 30)
                    await asyncio.sleep(timeout + 1)
            
            return await func(*args, **func_kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **func_kwargs) -> T:
            if settings.APP_ENV == "production":
                return func(*args, **func_kwargs)
            
            if random.random() < probability:
                if chaos_type == ChaosType.ERROR:
                    error_msg = kwargs.get("error_message", "Chaos induced error")
                    raise Exception(error_msg)
            
            return func(*args, **func_kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class RetryWithBackoff:
    """Advanced retry with exponential backoff and jitter."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay_seconds: float = 1.0,
        max_delay_seconds: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: tuple = (Exception,),
    ):
        """Initialize retry configuration.
        
        Args:
            max_retries: Maximum number of retries
            base_delay_seconds: Initial delay between retries
            max_delay_seconds: Maximum delay cap
            exponential_base: Base for exponential backoff
            jitter: Add random jitter to prevent thundering herd
            retryable_exceptions: Exceptions that trigger retry
        """
        self.max_retries = max_retries
        self.base_delay_seconds = base_delay_seconds
        self.max_delay_seconds = max_delay_seconds
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt.
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        delay = min(
            self.base_delay_seconds * (self.exponential_base ** attempt),
            self.max_delay_seconds
        )
        
        if self.jitter:
            delay *= (0.5 + random.random())
        
        return delay
    
    async def execute(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Last exception after all retries exhausted
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            
            except self.retryable_exceptions as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    delay = self.calculate_delay(attempt)
                    await asyncio.sleep(delay)
        
        raise last_exception


class DeadLetterQueue:
    """Dead letter queue for permanently failed tasks."""
    
    def __init__(self):
        self.redis = get_redis_client()
        self.key = "dead_letter_queue"
        self.key_metadata = "dead_letter_queue:metadata"
    
    def add(
        self,
        task_id: str,
        error: str,
        attempts: int,
        task_data: Dict[str, Any],
    ) -> bool:
        """Add a task to the dead letter queue.
        
        Args:
            task_id: Task ID
            error: Error message
            attempts: Number of attempts made
            task_data: Original task data
            
        Returns:
            True if added
        """
        import json
        
        entry = {
            "task_id": task_id,
            "error": error,
            "attempts": attempts,
            "task_data": task_data,
            "added_at": datetime.utcnow().isoformat(),
        }
        
        self.redis.lpush(self.key, json.dumps(entry))
        self.redis.hset(self.key_metadata, task_id, json.dumps(entry))
        
        return True
    
    def get_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get tasks from the dead letter queue.
        
        Args:
            limit: Maximum number to return
            
        Returns:
            List of DLQ entries
        """
        import json
        
        entries = self.redis.lrange(self.key, 0, limit - 1)
        return [json.loads(e) for e in entries]
    
    def requeue(self, task_id: str) -> bool:
        """Requeue a task from the dead letter queue.
        
        Args:
            task_id: Task ID to requeue
            
        Returns:
            True if requeued
        """
        import json
        
        entry_str = self.redis.hget(self.key_metadata, task_id)
        if entry_str:
            entry = json.loads(entry_str)
            self.redis.hdel(self.key_metadata, task_id)
            # Remove from list (expensive operation)
            self.redis.lrem(self.key, 1, entry_str)
            return True
        
        return False
    
    def get_count(self) -> int:
        """Get the count of tasks in the DLQ.
        
        Returns:
            Number of tasks in DLQ
        """
        return self.redis.llen(self.key)


# Singleton instance
_chaos_engine: Optional[ChaosEngineering] = None


def get_chaos_engine() -> ChaosEngineering:
    """Get chaos engineering singleton."""
    global _chaos_engine
    if _chaos_engine is None:
        _chaos_engine = ChaosEngineering()
    return _chaos_engine
