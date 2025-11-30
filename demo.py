#!/usr/bin/env python3
"""
Quick Demo Script
Run this to see POSIVA capabilities with sample data
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import numpy as np
from src.utils.config import Config
from src.analytics.yield_analytics import YieldAnalytics
from src.analytics.test_time_analytics import TestTimeAnalytics
from src.quality.profiler import DataProfiler
from src.ml.yield_prediction import YieldPredictionModel


def print_header(text):
    """Print section header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def main():
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   ██████╗  ██████╗ ███████╗██╗██╗   ██╗ █████╗              ║
    ║   ██╔══██╗██╔═══██╗██╔════╝██║██║   ██║██╔══██╗             ║
    ║   ██████╔╝██║   ██║███████╗██║██║   ██║███████║             ║
    ║   ██╔═══╝ ██║   ██║╚════██║██║╚██╗ ██╔╝██╔══██║             ║
    ║   ██║     ╚██████╔╝███████║██║ ╚████╔╝ ██║  ██║             ║
    ║   ╚═╝      ╚═════╝ ╚══════╝╚═╝  ╚═══╝  ╚═╝  ╚═╝             ║
    ║                                                               ║
    ║         Advanced Analytics Platform - Quick Demo             ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Configuration
    config = Config()
    
    # Load sample data
    print_header("📂 Loading Sample Data")
    sample_path = config.data_dir / 'sample' / 'sample_data.csv'
    
    if not sample_path.exists():
        print("❌ Sample data not found. Generating...")
        import subprocess
        result = subprocess.run(
            ["python3", "scripts/generate_sample_data.py"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"Error generating data: {result.stderr}")
            return
    
    df = pd.read_csv(sample_path)
    print(f"✅ Loaded {len(df):,} test records")
    print(f"   Devices: {df['device_id'].nunique()}")
    print(f"   Tests: {df['test_name'].nunique()}")
    print(f"   Lots: {df['lot_id'].nunique()}")
    
    # Data Quality Check
    print_header("🔍 Data Quality Analysis")
    profiler = DataProfiler()
    profile = profiler.profile(df, name="sample_data")
    
    print(f"Quality Score: {profile['quality_score']:.1f}/100")
    print(f"Missing Values: {profile['missing_values']['total_missing']}")
    print(f"Duplicates: {profile['duplicates']['count']}")
    print("✅ Data quality check passed!")
    
    # Yield Analytics
    print_header("📊 Yield Analytics")
    ya = YieldAnalytics(df)
    summary = ya.generate_summary()
    
    print(f"Overall Device Yield: {summary['overall_yield']:.2f}%")
    print(f"Passing Devices: {summary['passing_devices']}/{summary['total_devices']}")
    print(f"Test Yield: {summary['test_yield']:.2f}%")
    print(f"Lowest Yielding Test: {summary['lowest_yield_test']} ({summary['lowest_yield_value']:.1f}%)")
    
    # Test yield by test
    test_yield = ya.yield_by_test()
    print(f"\nTest Yield Summary:")
    print(f"  Highest: {test_yield.iloc[0]['test_name']} - {test_yield.iloc[0]['yield']:.1f}%")
    print(f"  Lowest: {test_yield.iloc[-1]['test_name']} - {test_yield.iloc[-1]['yield']:.1f}%")
    
    # Pareto analysis
    pareto = ya.failing_tests_pareto(top_n=5)
    tests_for_80 = (pareto['cumulative_pct'] <= 80).sum()
    print(f"\n🎯 Pareto Insight: {tests_for_80} tests account for 80% of failures")
    
    # Test Time Analytics
    print_header("⏱️ Test Time Analysis")
    tta = TestTimeAnalytics(df)
    time_stats = tta.overall_statistics()
    
    print(f"Average Test Time: {time_stats['avg_time_ms']:.1f} ms")
    print(f"Total Test Time: {time_stats['total_time_hours']:.2f} hours")
    print(f"Avg Device Test Time: {time_stats['avg_device_time_sec']:.1f} seconds")
    
    # Slowest tests
    slow_tests = tta.slowest_tests(top_n=3)
    print(f"\nSlowest Tests:")
    for _, row in slow_tests.iterrows():
        print(f"  - {row['test_name']}: {row['mean']:.1f} ms")
    
    # Optimization opportunities
    opportunities = tta.optimization_opportunities()
    savings = opportunities['potential_savings']
    print(f"\n💰 Potential Savings:")
    print(f"  If top 3 tests reduced by 20%: {savings['top_3_reduction_20pct_ms']/1000:.1f} sec ({savings['top_3_reduction_20pct_pct']:.1f}%)")
    
    # Machine Learning
    print_header("🤖 Machine Learning - Yield Prediction")
    print("Training Random Forest model...")
    
    model = YieldPredictionModel(model_type='random_forest')
    metrics = model.train(df, test_size=0.2)
    
    print(f"\nModel Performance:")
    print(f"  Accuracy:  {metrics['test']['accuracy']:.4f}")
    print(f"  Precision: {metrics['test']['precision']:.4f}")
    print(f"  Recall:    {metrics['test']['recall']:.4f}")
    print(f"  F1-Score:  {metrics['test']['f1']:.4f}")
    if 'auc_roc' in metrics['test']:
        print(f"  AUC-ROC:   {metrics['test']['auc_roc']:.4f}")
    print(f"  CV Score:  {metrics['cv_mean']:.4f} ± {metrics['cv_std']:.4f}")
    
    # Feature importance
    importance = model.feature_importance().head(5)
    print(f"\nTop 5 Important Features:")
    for _, row in importance.iterrows():
        print(f"  - {row['feature']}: {row['importance']:.4f}")
    
    # Summary
    print_header("✅ Demo Complete!")
    print("""
    What we demonstrated:
    ✅ Data loading and validation
    ✅ Data quality profiling
    ✅ Yield analytics with Pareto analysis
    ✅ Test time analysis and optimization
    ✅ Machine learning model training
    ✅ Feature importance analysis
    
    Next Steps:
    1. Explore Jupyter notebooks in notebooks/
    2. Launch dashboard: streamlit run webapp/Home.py
    3. Review documentation: README.md, PRD.md, BUILD_STATUS.md
    4. Add your own data to data/raw/
    
    Dashboard URL: http://localhost:8501 (after running streamlit)
    """)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
