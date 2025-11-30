"""
Unit tests for analytics modules
"""

import pytest
import pandas as pd
import numpy as np
import sys
sys.path.append('.')

from src.analytics.yield_analytics import YieldAnalyzer
from src.analytics.test_time_analysis import TestTimeAnalyzer
from src.quality.data_quality import DataQualityChecker

# Sample data fixture
@pytest.fixture
def sample_data():
    """Create sample test data"""
    np.random.seed(42)
    return pd.DataFrame({
        'Device_ID': range(100),
        'Test_Result': np.random.choice(['PASS', 'FAIL'], 100, p=[0.95, 0.05]),
        'Test_Time_sec': np.random.uniform(1, 5, 100),
        'Wafer_ID': [f'W{i//25:03d}' for i in range(100)],
        'Lot_ID': [f'L{i//50:03d}' for i in range(100)]
    })

def test_yield_analyzer(sample_data):
    """Test YieldAnalyzer"""
    analyzer = YieldAnalyzer(sample_data)
    
    # Test overall yield
    overall = analyzer.overall_yield()
    assert 'Yield %' in overall
    assert 0 <= overall['Yield %'] <= 100
    
    # Test yield by wafer
    by_wafer = analyzer.yield_by_wafer()
    assert len(by_wafer) > 0
    assert 'Wafer_ID' in by_wafer.columns

def test_test_time_analyzer(sample_data):
    """Test TestTimeAnalyzer"""
    analyzer = TestTimeAnalyzer(sample_data)
    
    # Test statistics
    stats = analyzer.statistics()
    assert 'mean' in stats
    assert 'median' in stats
    assert 'std' in stats

def test_data_quality_checker(sample_data):
    """Test DataQualityChecker"""
    checker = DataQualityChecker(sample_data)
    
    # Test quality score
    score = checker.quality_score()
    assert 0 <= score <= 100
    
    # Test missing values
    missing = checker.missing_values()
    assert isinstance(missing, pd.Series)
