"""
Configuration management for POSIVA Analytics Platform
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(False, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # Paths
    base_dir: Path = Path(__file__).parent.parent.parent
    data_path: Path = Field(None, env="DATA_PATH")
    models_path: Path = Field(None, env="MODELS_PATH")
    logs_path: Path = Field(None, env="LOGS_PATH")
    
    # Database
    postgres_host: str = Field("localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(5432, env="POSTGRES_PORT")
    postgres_db: str = Field("posiva", env="POSTGRES_DB")
    postgres_user: str = Field("posiva_user", env="POSTGRES_USER")
    postgres_password: str = Field("", env="POSTGRES_PASSWORD")
    
    # Redis
    redis_host: str = Field("localhost", env="REDIS_HOST")
    redis_port: int = Field(6379, env="REDIS_PORT")
    redis_password: Optional[str] = Field(None, env="REDIS_PASSWORD")
    
    # Security
    secret_key: str = Field("dev-secret-key", env="SECRET_KEY")
    jwt_secret: str = Field("dev-jwt-secret", env="JWT_SECRET")
    allowed_hosts: list = Field(["*"], env="ALLOWED_HOSTS")
    
    # API
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")
    api_workers: int = Field(4, env="API_WORKERS")
    
    # MLflow
    mlflow_tracking_uri: str = Field("http://localhost:5000", env="MLFLOW_TRACKING_URI")
    mlflow_artifact_root: str = Field("/mlflow/artifacts", env="MLFLOW_ARTIFACT_ROOT")
    
    # Email
    smtp_host: Optional[str] = Field(None, env="SMTP_HOST")
    smtp_port: int = Field(587, env="SMTP_PORT")
    smtp_user: Optional[str] = Field(None, env="SMTP_USER")
    smtp_password: Optional[str] = Field(None, env="SMTP_PASSWORD")
    alert_email: Optional[str] = Field(None, env="ALERT_EMAIL")
    
    # Cloud
    aws_access_key_id: Optional[str] = Field(None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(None, env="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field("us-east-1", env="AWS_REGION")
    aws_s3_bucket: Optional[str] = Field(None, env="AWS_S3_BUCKET")
    
    # Feature flags
    enable_caching: bool = Field(True, env="ENABLE_CACHING")
    enable_monitoring: bool = Field(True, env="ENABLE_MONITORING")
    enable_auto_training: bool = Field(False, env="ENABLE_AUTO_TRAINING")
    enable_email_alerts: bool = Field(False, env="ENABLE_EMAIL_ALERTS")
    
    # Model settings
    default_model: str = Field("random_forest", env="DEFAULT_MODEL")
    auto_retrain_threshold: float = Field(0.85, env="AUTO_RETRAIN_THRESHOLD")
    min_training_samples: int = Field(1000, env="MIN_TRAINING_SAMPLES")
    
    # Performance
    cache_ttl: int = Field(3600, env="CACHE_TTL")
    max_concurrent_requests: int = Field(100, env="MAX_CONCURRENT_REQUESTS")
    request_timeout: int = Field(30, env="REQUEST_TIMEOUT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Set default paths if not provided
        if self.data_path is None:
            self.data_path = self.base_dir / "data"
        if self.models_path is None:
            self.models_path = self.base_dir / "models"
        if self.logs_path is None:
            self.logs_path = self.base_dir / "logs"
        
        # Create directories if they don't exist
        self.data_path.mkdir(exist_ok=True)
        self.models_path.mkdir(exist_ok=True)
        self.logs_path.mkdir(exist_ok=True)
    
    @property
    def database_url(self) -> str:
        """Get database connection URL"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def redis_url(self) -> str:
        """Get Redis connection URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}"
        return f"redis://{self.redis_host}:{self.redis_port}"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment.lower() == "development"

# Global settings instance
settings = Settings()
