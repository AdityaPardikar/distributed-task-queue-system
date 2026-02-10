"""System status monitoring for comprehensive health checks and metrics."""

import os
import platform
import psutil
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import text, func

from src.cache.client import get_redis_client
from src.config import get_settings
from src.models import Task, Worker, Campaign


settings = get_settings()


class SystemStatusMonitor:
    """Monitor and collect system health metrics."""

    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get basic system information."""
        return {
            "hostname": platform.node(),
            "os": platform.system(),
            "os_version": platform.release(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
            "cpu_count": psutil.cpu_count(),
            "architecture": platform.machine(),
        }

    @staticmethod
    def get_resource_usage() -> Dict[str, Any]:
        """Get current resource usage metrics."""
        memory = psutil.virtual_memory()
        # Use appropriate path for disk usage based on OS
        disk_path = "C:\\" if platform.system() == "Windows" else "/"
        try:
            disk = psutil.disk_usage(disk_path)
        except Exception:
            # Fallback
            disk = psutil.disk_usage(os.getcwd()[:2] + "\\" if platform.system() == "Windows" else "/")
        cpu_percent = psutil.cpu_percent(interval=0.1)

        return {
            "cpu": {
                "percent": cpu_percent,
                "count": psutil.cpu_count(),
                "load_avg": getattr(psutil, "getloadavg", lambda: (0, 0, 0))(),
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "percent": memory.percent,
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "percent": disk.percent,
            },
        }

    @staticmethod
    def check_database_health(db: Session) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        start = datetime.utcnow()
        try:
            db.execute(text("SELECT 1"))
            latency = (datetime.utcnow() - start).total_seconds() * 1000
            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "connected": True,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "connected": False,
            }

    @staticmethod
    def check_redis_health() -> Dict[str, Any]:
        """Check Redis connectivity and performance."""
        start = datetime.utcnow()
        try:
            redis = get_redis_client()
            redis.ping()
            info = redis.info() if hasattr(redis, "info") else {}
            latency = (datetime.utcnow() - start).total_seconds() * 1000
            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "connected": True,
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "connected": False,
            }

    @staticmethod
    def get_task_statistics(db: Session) -> Dict[str, Any]:
        """Get task queue statistics."""
        try:
            total_tasks = db.query(func.count(Task.task_id)).scalar() or 0
            pending = db.query(func.count(Task.task_id)).filter(Task.status == "PENDING").scalar() or 0
            running = db.query(func.count(Task.task_id)).filter(Task.status == "RUNNING").scalar() or 0
            completed = db.query(func.count(Task.task_id)).filter(Task.status == "COMPLETED").scalar() or 0
            failed = db.query(func.count(Task.task_id)).filter(Task.status == "FAILED").scalar() or 0

            # Calculate success rate
            finished = completed + failed
            success_rate = (completed / finished * 100) if finished > 0 else 100.0

            # Get tasks created in last hour
            hour_ago = datetime.utcnow() - timedelta(hours=1)
            tasks_last_hour = db.query(func.count(Task.task_id)).filter(
                Task.created_at >= hour_ago
            ).scalar() or 0

            return {
                "total": total_tasks,
                "pending": pending,
                "running": running,
                "completed": completed,
                "failed": failed,
                "success_rate": round(success_rate, 2),
                "tasks_last_hour": tasks_last_hour,
                "queue_depth": pending + running,
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_worker_statistics(db: Session) -> Dict[str, Any]:
        """Get worker pool statistics."""
        try:
            threshold = datetime.utcnow() - timedelta(seconds=settings.WORKER_DEAD_TIMEOUT_SECONDS)
            
            total = db.query(func.count(Worker.worker_id)).scalar() or 0
            active = db.query(func.count(Worker.worker_id)).filter(
                Worker.status == "ACTIVE",
                Worker.last_heartbeat >= threshold
            ).scalar() or 0
            
            # Get total capacity and current load
            capacity_result = db.query(
                func.sum(Worker.capacity),
                func.sum(Worker.current_load)
            ).filter(Worker.status == "ACTIVE").first()
            
            total_capacity = capacity_result[0] or 0
            total_load = capacity_result[1] or 0
            utilization = (total_load / total_capacity * 100) if total_capacity > 0 else 0

            return {
                "total": total,
                "active": active,
                "inactive": total - active,
                "total_capacity": total_capacity,
                "current_load": total_load,
                "utilization_percent": round(utilization, 2),
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_campaign_statistics(db: Session) -> Dict[str, Any]:
        """Get email campaign statistics."""
        try:
            total = db.query(func.count(Campaign.campaign_id)).scalar() or 0
            active = db.query(func.count(Campaign.campaign_id)).filter(
                Campaign.status == "ACTIVE"
            ).scalar() or 0
            completed = db.query(func.count(Campaign.campaign_id)).filter(
                Campaign.status == "COMPLETED"
            ).scalar() or 0

            return {
                "total": total,
                "active": active,
                "completed": completed,
                "draft": total - active - completed,
            }
        except Exception as e:
            return {"error": str(e)}

    @classmethod
    def get_full_status(cls, db: Session) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.VERSION,
            "environment": settings.APP_ENV,
            "system": cls.get_system_info(),
            "resources": cls.get_resource_usage(),
            "dependencies": {
                "database": cls.check_database_health(db),
                "redis": cls.check_redis_health(),
            },
            "metrics": {
                "tasks": cls.get_task_statistics(db),
                "workers": cls.get_worker_statistics(db),
                "campaigns": cls.get_campaign_statistics(db),
            },
            "health_score": cls._calculate_health_score(db),
        }

    @classmethod
    def _calculate_health_score(cls, db: Session) -> Dict[str, Any]:
        """Calculate overall health score (0-100)."""
        score = 100
        issues = []

        # Check database
        db_health = cls.check_database_health(db)
        if db_health["status"] != "healthy":
            score -= 40
            issues.append("Database unhealthy")
        elif db_health.get("latency_ms", 0) > 100:
            score -= 10
            issues.append("Database slow (>100ms)")

        # Check Redis
        redis_health = cls.check_redis_health()
        if redis_health["status"] != "healthy":
            score -= 30
            issues.append("Redis unhealthy")

        # Check resource usage
        resources = cls.get_resource_usage()
        if resources["cpu"]["percent"] > 90:
            score -= 10
            issues.append("High CPU usage (>90%)")
        if resources["memory"]["percent"] > 90:
            score -= 10
            issues.append("High memory usage (>90%)")
        if resources["disk"]["percent"] > 90:
            score -= 10
            issues.append("High disk usage (>90%)")

        # Check worker health
        workers = cls.get_worker_statistics(db)
        if workers.get("active", 0) == 0:
            score -= 20
            issues.append("No active workers")
        elif workers.get("utilization_percent", 0) > 95:
            score -= 5
            issues.append("High worker utilization (>95%)")

        return {
            "score": max(0, score),
            "status": "healthy" if score >= 80 else "degraded" if score >= 50 else "critical",
            "issues": issues,
        }
