"""Retry strategy implementations for failed tasks."""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class RetryStrategy(str, Enum):
    """Retry strategy types."""
    IMMEDIATE = "immediate"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    CUSTOM = "custom"


class RetryCalculator:
    """Calculate retry delays and next retry times based on strategy."""
    
    @staticmethod
    def calculate_delay(
        retry_count: int,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        base_delay_seconds: int = 2,
        max_delay_seconds: int = 3600,
        linear_increment: int = 10
    ) -> int:
        """
        Calculate retry delay in seconds.
        
        Args:
            retry_count: Number of retries so far
            strategy: Retry strategy to use
            base_delay_seconds: Base delay for exponential/linear strategies
            max_delay_seconds: Maximum delay cap (default 1 hour)
            linear_increment: Increment for linear strategy
        
        Returns:
            Delay in seconds before next retry
        """
        if strategy == RetryStrategy.IMMEDIATE:
            return 0
        
        elif strategy == RetryStrategy.LINEAR:
            # Linear: base_delay + (retry_count * linear_increment)
            delay = base_delay_seconds + (retry_count * linear_increment)
            return min(delay, max_delay_seconds)
        
        elif strategy == RetryStrategy.EXPONENTIAL:
            # Exponential: base_delay * 2^retry_count
            delay = base_delay_seconds * (2 ** retry_count)
            return min(delay, max_delay_seconds)
        
        else:  # CUSTOM or unknown
            # Default to exponential
            delay = base_delay_seconds * (2 ** retry_count)
            return min(delay, max_delay_seconds)
    
    @staticmethod
    def calculate_next_retry_at(
        retry_count: int,
        current_time: Optional[datetime] = None,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        base_delay_seconds: int = 2,
        max_delay_seconds: int = 3600,
        linear_increment: int = 10
    ) -> datetime:
        """
        Calculate the next retry timestamp.
        
        Args:
            retry_count: Number of retries so far
            current_time: Current time (defaults to now)
            strategy: Retry strategy to use
            base_delay_seconds: Base delay for exponential/linear strategies
            max_delay_seconds: Maximum delay cap
            linear_increment: Increment for linear strategy
        
        Returns:
            Timestamp for next retry attempt
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        delay_seconds = RetryCalculator.calculate_delay(
            retry_count,
            strategy,
            base_delay_seconds,
            max_delay_seconds,
            linear_increment
        )
        
        return current_time + timedelta(seconds=delay_seconds)
    
    @staticmethod
    def should_retry(
        retry_count: int,
        max_retries: int,
        error_type: Optional[str] = None,
        non_retryable_errors: Optional[list] = None
    ) -> bool:
        """
        Determine if a task should be retried.
        
        Args:
            retry_count: Current retry count
            max_retries: Maximum allowed retries
            error_type: Type of error that occurred
            non_retryable_errors: List of error types that should not be retried
        
        Returns:
            True if task should be retried, False otherwise
        """
        # Check if we've exceeded max retries
        if retry_count >= max_retries:
            return False
        
        # Check if error type is non-retryable
        if non_retryable_errors and error_type:
            if error_type in non_retryable_errors:
                return False
        
        return True
    
    @staticmethod
    def get_retry_delay_schedule(
        max_retries: int,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        base_delay_seconds: int = 2,
        max_delay_seconds: int = 3600
    ) -> list[int]:
        """
        Get a schedule of retry delays for all attempts.
        
        Args:
            max_retries: Maximum number of retries
            strategy: Retry strategy to use
            base_delay_seconds: Base delay
            max_delay_seconds: Maximum delay cap
        
        Returns:
            List of delay durations in seconds for each retry
        """
        schedule = []
        for retry_count in range(max_retries):
            delay = RetryCalculator.calculate_delay(
                retry_count,
                strategy,
                base_delay_seconds,
                max_delay_seconds
            )
            schedule.append(delay)
        return schedule


# Common non-retryable error types
NON_RETRYABLE_ERRORS = [
    "ValidationError",
    "AuthenticationError",
    "PermissionDeniedError",
    "ResourceNotFoundError",
    "InvalidInputError"
]


def format_retry_schedule(schedule: list[int]) -> str:
    """
    Format retry schedule for display.
    
    Args:
        schedule: List of delay durations in seconds
    
    Returns:
        Formatted string representation
    """
    formatted = []
    for i, delay in enumerate(schedule):
        if delay < 60:
            formatted.append(f"Retry {i+1}: {delay}s")
        elif delay < 3600:
            formatted.append(f"Retry {i+1}: {delay//60}m {delay%60}s")
        else:
            formatted.append(f"Retry {i+1}: {delay//3600}h {(delay%3600)//60}m")
    return " | ".join(formatted)
