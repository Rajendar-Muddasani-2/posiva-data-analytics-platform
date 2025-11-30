"""
Configuration Management Module
Handles loading and accessing configuration settings
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration manager for POSIVA Analytics Platform"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration
        
        Args:
            config_file: Path to YAML config file (optional)
        """
        self.project_root = Path(__file__).parent.parent.parent
        self.config_data = {}
        
        # Load from YAML if provided
        if config_file and Path(config_file).exists():
            with open(config_file, 'r') as f:
                self.config_data = yaml.safe_load(f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key (supports dot notation: 'database.host')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        # Try environment variable first
        env_value = os.getenv(key.upper().replace('.', '_'))
        if env_value is not None:
            return env_value
        
        # Try config file
        keys = key.split('.')
        value = self.config_data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        return value if value is not None else default
    
    @property
    def data_raw_path(self) -> Path:
        """Path to raw data directory"""
        path = self.get('DATA_RAW_PATH', './data/raw')
        return self.project_root / path
    
    @property
    def data_processed_path(self) -> Path:
        """Path to processed data directory"""
        path = self.get('DATA_PROCESSED_PATH', './data/processed')
        return self.project_root / path
    
    @property
    def data_features_path(self) -> Path:
        """Path to features directory"""
        path = self.get('DATA_FEATURES_PATH', './data/features')
        return self.project_root / path
    
    @property
    def model_path(self) -> Path:
        """Path to models directory"""
        path = self.get('MODEL_PATH', './models')
        return self.project_root / path
    
    @property
    def reports_path(self) -> Path:
        """Path to reports directory"""
        path = self.get('REPORTS_PATH', './reports')
        return self.project_root / path
    
    @property
    def debug(self) -> bool:
        """Debug mode flag"""
        return self.get('DEBUG', 'False').lower() == 'true'
    
    @property
    def log_level(self) -> str:
        """Logging level"""
        return self.get('LOG_LEVEL', 'INFO')
    
    @property
    def n_jobs(self) -> int:
        """Number of parallel jobs"""
        n = self.get('N_JOBS', '-1')
        return int(n)
    
    @property
    def batch_size(self) -> int:
        """Batch size for processing"""
        return int(self.get('BATCH_SIZE', '10000'))
    
    def __repr__(self) -> str:
        return f"Config(project_root={self.project_root})"


# Global config instance
config = Config()
