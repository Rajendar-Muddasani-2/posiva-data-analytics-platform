"""
Test Configuration Module
"""

import pytest
from src.utils.config import Config


def test_config_initialization():
    """Test config can be initialized"""
    config = Config()
    assert config is not None
    assert config.project_root.exists()


def test_config_paths():
    """Test config paths are correct"""
    config = Config()
    assert config.data_raw_path.name == 'raw'
    assert config.data_processed_path.name == 'processed'
    assert config.model_path.name == 'models'


def test_config_defaults():
    """Test default values"""
    config = Config()
    assert config.log_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR']
    assert isinstance(config.n_jobs, int)
    assert isinstance(config.batch_size, int)
