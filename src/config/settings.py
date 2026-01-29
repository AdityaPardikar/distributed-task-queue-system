"""Application settings and configuration"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Application
    APP_NAME: str = "TaskFlow"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-change-in-production"
    VERSION: str = "0.1.0"

    # Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DASHBOARD_URL: str = "http://localhost:3000"
    API_BASE_URL: str = "http://localhost:8000"

    # Database
    DATABASE_URL: str = "postgresql://taskflow:password@localhost:5432/taskflow"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_MAX_CONNECTIONS: int = 50

    # JWT
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    JWT_REFRESH_EXPIRATION_DAYS: int = 30

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100
    RATE_LIMIT_REQUESTS_PER_HOUR: int = 1000

    # Worker Settings
    WORKER_CAPACITY: int = 5
    WORKER_TIMEOUT_SECONDS: int = 300
    WORKER_MAX_RETRIES: int = 5
    WORKER_RETRY_BACKOFF_SECONDS: int = 2
    WORKER_HEARTBEAT_INTERVAL_SECONDS: int = 10
    WORKER_DEAD_TIMEOUT_SECONDS: int = 30

    # Task Settings
    TASK_DEFAULT_PRIORITY: int = 5
    TASK_MIN_PRIORITY: int = 1
    TASK_MAX_PRIORITY: int = 10

    # Email Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "your-email@gmail.com"
    SMTP_PASSWORD: str = "your-app-password"
    SMTP_FROM_EMAIL: str = "noreply@taskflow.io"
    SMTP_FROM_NAME: str = "TaskFlow"
    SMTP_USE_TLS: bool = True
    SMTP_TIMEOUT_SECONDS: int = 10
    SMTP_CONNECTION_POOL_SIZE: int = 5

    # Campaign Settings
    CAMPAIGN_DEFAULT_RATE_LIMIT: int = 100
    CAMPAIGN_MAX_RATE_LIMIT: int = 1000

    # Monitoring
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Security
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:8000"
    ALLOWED_HOSTS: str = "localhost,127.0.0.1"

    # Observability
    TRACING_ENABLED: bool = False
    TRACING_ENDPOINT: Optional[str] = None
    METRICS_ENABLED: bool = True

    # Feature Flags
    ENABLE_CAMPAIGNS: bool = True
    ENABLE_SCHEDULING: bool = True
    ENABLE_DEPENDENCIES: bool = True
    ENABLE_DLQ: bool = True
    ENABLE_HEALTH_CHECK: bool = True

    # Testing
    TESTING: bool = False
    TEST_DATABASE_URL: str = "postgresql://taskflow:password@localhost:5432/taskflow_test"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def allowed_hosts_list(self) -> list[str]:
        """Parse allowed hosts from comma-separated string"""
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.APP_ENV == "development"

    @property
    def is_testing(self) -> bool:
        """Check if running tests"""
        return self.TESTING


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
