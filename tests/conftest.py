"""
Pytest configuration
"""

import pytest
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_data_path():
    """Fixture for sample data path"""
    return project_root / "data" / "sample" / "sample_data.csv"
