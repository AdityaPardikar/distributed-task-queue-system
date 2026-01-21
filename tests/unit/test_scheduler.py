"""Unit tests for task scheduler."""

import pytest
from datetime import datetime, timedelta
from src.core.scheduler import TaskScheduler


class TestTaskScheduler:
    """Test cases for task scheduler."""
    
    def test_validate_cron_expression_valid(self):
        """Test validation of valid cron expressions."""
        scheduler = TaskScheduler()
        
        # Every hour
        assert scheduler.validate_cron_expression("0 * * * *") is True
        
        # Every 6 hours
        assert scheduler.validate_cron_expression("0 */6 * * *") is True
        
        # Every day at midnight
        assert scheduler.validate_cron_expression("0 0 * * *") is True
        
        # Every Monday at 9 AM
        assert scheduler.validate_cron_expression("0 9 * * 1") is True
    
    def test_validate_cron_expression_invalid(self):
        """Test validation of invalid cron expressions."""
        scheduler = TaskScheduler()
        
        # Invalid format
        assert scheduler.validate_cron_expression("invalid") is False
        
        # Too many fields
        assert scheduler.validate_cron_expression("* * * * * *") is False
        
        # Out of range values
        assert scheduler.validate_cron_expression("61 * * * *") is False
    
    def test_get_next_run_time_hourly(self):
        """Test calculating next run time for hourly cron."""
        scheduler = TaskScheduler()
        
        # Every hour at minute 0
        base_time = datetime(2026, 1, 21, 10, 30, 0)
        next_run = scheduler.get_next_run_time("0 * * * *", base_time)
        
        assert next_run is not None
        assert next_run == datetime(2026, 1, 21, 11, 0, 0)
    
    def test_get_next_run_time_daily(self):
        """Test calculating next run time for daily cron."""
        scheduler = TaskScheduler()
        
        # Every day at midnight
        base_time = datetime(2026, 1, 21, 10, 30, 0)
        next_run = scheduler.get_next_run_time("0 0 * * *", base_time)
        
        assert next_run is not None
        assert next_run == datetime(2026, 1, 22, 0, 0, 0)
    
    def test_get_next_run_time_every_6_hours(self):
        """Test calculating next run time for every 6 hours."""
        scheduler = TaskScheduler()
        
        # Every 6 hours
        base_time = datetime(2026, 1, 21, 10, 0, 0)
        next_run = scheduler.get_next_run_time("0 */6 * * *", base_time)
        
        assert next_run is not None
        assert next_run == datetime(2026, 1, 21, 12, 0, 0)
    
    def test_get_next_run_time_weekly(self):
        """Test calculating next run time for weekly cron."""
        scheduler = TaskScheduler()
        
        # Every Monday at 9 AM (day 1)
        base_time = datetime(2026, 1, 21, 10, 0, 0)  # Wednesday
        next_run = scheduler.get_next_run_time("0 9 * * 1", base_time)
        
        assert next_run is not None
        # Next Monday after Wednesday Jan 21
        assert next_run == datetime(2026, 1, 26, 9, 0, 0)
    
    def test_get_next_run_time_invalid_expression(self):
        """Test that invalid cron expression returns None."""
        scheduler = TaskScheduler()
        
        next_run = scheduler.get_next_run_time("invalid cron", datetime.utcnow())
        assert next_run is None
    
    def test_get_next_run_time_defaults_to_now(self):
        """Test that get_next_run_time defaults to current time."""
        scheduler = TaskScheduler()
        
        # Should not raise an error
        next_run = scheduler.get_next_run_time("0 * * * *")
        assert next_run is not None
        assert next_run > datetime.utcnow()
    
    def test_scheduler_initialization(self):
        """Test scheduler initialization."""
        scheduler = TaskScheduler(poll_interval=30)
        
        assert scheduler.poll_interval == 30
        assert scheduler.running is False
        assert scheduler.broker is not None
    
    def test_scheduler_default_poll_interval(self):
        """Test default poll interval."""
        scheduler = TaskScheduler()
        
        assert scheduler.poll_interval == 60
