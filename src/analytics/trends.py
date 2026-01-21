"""Analytics module for task trends and performance analysis."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models import Task


class TaskAnalytics:
    """Analyze task completion trends and performance patterns."""

    @staticmethod
    def get_completion_rate_trend(
        db: Session,
        hours: int = 24,
        interval_minutes: int = 60,
    ) -> List[Dict]:
        """Get task completion rate trends over time.
        
        Args:
            db: Database session
            hours: Number of hours to analyze (default 24)
            interval_minutes: Time interval for aggregation (default 60 = hourly)
            
        Returns:
            List of trend data points with timestamp, completed, and failed counts
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        tasks = db.query(Task).filter(Task.completed_at >= cutoff).all()
        
        # Group by interval
        trends = {}
        for task in tasks:
            if not task.completed_at:
                continue
            
            # Calculate bucket key based on interval
            bucket_seconds = interval_minutes * 60
            timestamp = int(task.completed_at.timestamp())
            bucket_key = (timestamp // bucket_seconds) * bucket_seconds
            bucket_time = datetime.utcfromtimestamp(bucket_key)
            time_str = bucket_time.isoformat()
            
            if time_str not in trends:
                trends[time_str] = {
                    "timestamp": time_str,
                    "completed": 0,
                    "failed": 0,
                    "rate": 0.0,
                }
            
            if task.status == "COMPLETED":
                trends[time_str]["completed"] += 1
            elif task.status == "FAILED":
                trends[time_str]["failed"] += 1
        
        # Calculate rates
        for trend in trends.values():
            total = trend["completed"] + trend["failed"]
            trend["rate"] = trend["completed"] / total if total > 0 else 0.0
        
        return sorted(trends.values(), key=lambda x: x["timestamp"])

    @staticmethod
    def get_average_wait_time_trend(
        db: Session,
        hours: int = 24,
        interval_minutes: int = 60,
    ) -> List[Dict]:
        """Get average task wait time trends (time from creation to start).
        
        Args:
            db: Database session
            hours: Number of hours to analyze
            interval_minutes: Time interval for aggregation
            
        Returns:
            List of trend data with average wait time per interval
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        tasks = (
            db.query(Task)
            .filter(
                Task.started_at >= cutoff,
                Task.started_at.isnot(None),
                Task.created_at.isnot(None),
            )
            .all()
        )
        
        # Group by interval
        trends = {}
        for task in tasks:
            wait_time = (task.started_at - task.created_at).total_seconds()
            
            bucket_seconds = interval_minutes * 60
            timestamp = int(task.started_at.timestamp())
            bucket_key = (timestamp // bucket_seconds) * bucket_seconds
            bucket_time = datetime.utcfromtimestamp(bucket_key)
            time_str = bucket_time.isoformat()
            
            if time_str not in trends:
                trends[time_str] = {
                    "timestamp": time_str,
                    "wait_times": [],
                    "min_wait": 0.0,
                    "max_wait": 0.0,
                    "avg_wait": 0.0,
                }
            
            trends[time_str]["wait_times"].append(wait_time)
        
        # Calculate statistics
        for trend in trends.values():
            if trend["wait_times"]:
                trend["min_wait"] = min(trend["wait_times"])
                trend["max_wait"] = max(trend["wait_times"])
                trend["avg_wait"] = sum(trend["wait_times"]) / len(trend["wait_times"])
            del trend["wait_times"]  # Remove raw data
        
        return sorted(trends.values(), key=lambda x: x["timestamp"])

    @staticmethod
    def get_peak_load_times(
        db: Session,
        hours: int = 24,
        interval_minutes: int = 60,
        top_n: int = 5,
    ) -> List[Dict]:
        """Identify peak load times by task submission rate.
        
        Args:
            db: Database session
            hours: Number of hours to analyze
            interval_minutes: Time interval for aggregation
            top_n: Number of top peak times to return
            
        Returns:
            List of top N peak load times with submission counts
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        tasks = db.query(Task).filter(Task.created_at >= cutoff).all()
        
        # Group by interval
        load_data = {}
        for task in tasks:
            bucket_seconds = interval_minutes * 60
            timestamp = int(task.created_at.timestamp())
            bucket_key = (timestamp // bucket_seconds) * bucket_seconds
            bucket_time = datetime.utcfromtimestamp(bucket_key)
            time_str = bucket_time.isoformat()
            
            if time_str not in load_data:
                load_data[time_str] = {
                    "timestamp": time_str,
                    "submitted": 0,
                }
            
            load_data[time_str]["submitted"] += 1
        
        # Sort and return top N
        sorted_loads = sorted(
            load_data.values(),
            key=lambda x: x["submitted"],
            reverse=True
        )
        
        return sorted_loads[:top_n]

    @staticmethod
    def get_task_type_distribution(
        db: Session,
        hours: int = 24,
    ) -> List[Dict]:
        """Get distribution of tasks by type.
        
        Args:
            db: Database session
            hours: Number of hours to analyze
            
        Returns:
            List of task types with counts and percentages
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        tasks = db.query(Task).filter(Task.created_at >= cutoff).all()
        
        distribution = {}
        for task in tasks:
            task_name = task.task_name
            
            if task_name not in distribution:
                distribution[task_name] = {
                    "task_name": task_name,
                    "total": 0,
                    "completed": 0,
                    "failed": 0,
                    "pending": 0,
                }
            
            distribution[task_name]["total"] += 1
            if task.status == "COMPLETED":
                distribution[task_name]["completed"] += 1
            elif task.status == "FAILED":
                distribution[task_name]["failed"] += 1
            elif task.status == "PENDING":
                distribution[task_name]["pending"] += 1
        
        # Calculate percentages
        total_tasks = sum(d["total"] for d in distribution.values())
        for dist in distribution.values():
            dist["percentage"] = (dist["total"] / total_tasks * 100) if total_tasks > 0 else 0.0
        
        return sorted(distribution.values(), key=lambda x: x["total"], reverse=True)

    @staticmethod
    def get_failed_task_patterns(
        db: Session,
        hours: int = 24,
        limit: int = 10,
    ) -> List[Dict]:
        """Identify patterns in failed tasks.
        
        Args:
            db: Database session
            hours: Number of hours to analyze
            limit: Maximum number of patterns to return
            
        Returns:
            List of most common failure patterns
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        failed_tasks = (
            db.query(Task)
            .filter(
                Task.status == "FAILED",
                Task.completed_at >= cutoff,
            )
            .all()
        )
        
        # Group by task name and error
        patterns = {}
        for task in failed_tasks:
            key = f"{task.task_name}:{task.error_message or 'Unknown'}"
            
            if key not in patterns:
                patterns[key] = {
                    "task_name": task.task_name,
                    "error": task.error_message or "Unknown",
                    "count": 0,
                    "last_occurrence": None,
                }
            
            patterns[key]["count"] += 1
            patterns[key]["last_occurrence"] = task.completed_at
        
        # Sort by count
        sorted_patterns = sorted(
            patterns.values(),
            key=lambda x: x["count"],
            reverse=True
        )
        
        return sorted_patterns[:limit]

    @staticmethod
    def get_retry_success_rate(
        db: Session,
        hours: int = 24,
    ) -> Dict:
        """Get retry success rate by task type.
        
        Args:
            db: Database session
            hours: Number of hours to analyze
            
        Returns:
            Dictionary with retry statistics by task type
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        tasks = (
            db.query(Task)
            .filter(
                Task.created_at >= cutoff,
                Task.retry_count > 0,
            )
            .all()
        )
        
        retry_stats = {}
        for task in tasks:
            task_name = task.task_name
            
            if task_name not in retry_stats:
                retry_stats[task_name] = {
                    "task_name": task_name,
                    "total_retries": 0,
                    "successful_after_retry": 0,
                    "failed_after_retry": 0,
                }
            
            retry_stats[task_name]["total_retries"] += task.retry_count
            
            if task.status == "COMPLETED":
                retry_stats[task_name]["successful_after_retry"] += 1
            elif task.status == "FAILED":
                retry_stats[task_name]["failed_after_retry"] += 1
        
        # Calculate success rates
        for stats in retry_stats.values():
            total = stats["successful_after_retry"] + stats["failed_after_retry"]
            stats["success_rate"] = (
                stats["successful_after_retry"] / total * 100
                if total > 0
                else 0.0
            )
            stats["avg_retries"] = (
                stats["total_retries"] / total
                if total > 0
                else 0.0
            )
        
        return retry_stats

    @staticmethod
    def get_performance_summary(db: Session) -> Dict:
        """Get comprehensive performance summary.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with overall performance metrics
        """
        all_tasks = db.query(Task).all()
        
        if not all_tasks:
            return {
                "total_tasks": 0,
                "completion_rate": 0.0,
                "failure_rate": 0.0,
                "avg_execution_time": 0.0,
                "avg_wait_time": 0.0,
                "total_retries": 0,
            }
        
        completed = [t for t in all_tasks if t.status == "COMPLETED"]
        failed = [t for t in all_tasks if t.status == "FAILED"]
        
        # Calculate metrics
        completion_rate = len(completed) / len(all_tasks) * 100 if all_tasks else 0
        failure_rate = len(failed) / len(all_tasks) * 100 if all_tasks else 0
        
        # Average execution time
        exec_times = [
            (t.completed_at - t.started_at).total_seconds()
            for t in completed
            if t.completed_at and t.started_at
        ]
        avg_exec_time = sum(exec_times) / len(exec_times) if exec_times else 0
        
        # Average wait time
        wait_times = [
            (t.started_at - t.created_at).total_seconds()
            for t in all_tasks
            if t.started_at and t.created_at
        ]
        avg_wait_time = sum(wait_times) / len(wait_times) if wait_times else 0
        
        # Total retries
        total_retries = sum(t.retry_count for t in all_tasks)
        
        return {
            "total_tasks": len(all_tasks),
            "completion_rate": round(completion_rate, 2),
            "failure_rate": round(failure_rate, 2),
            "avg_execution_time": round(avg_exec_time, 2),
            "avg_wait_time": round(avg_wait_time, 2),
            "total_retries": total_retries,
        }
