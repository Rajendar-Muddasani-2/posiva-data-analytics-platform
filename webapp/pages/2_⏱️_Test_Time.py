"""
Test Time Analytics Dashboard Page
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.analytics.test_time_analytics import TestTimeAnalytics
from src.utils.config import Config

st.set_page_config(page_title="Test Time Analytics", page_icon="⏱️", layout="wide")

# Header
st.title("⏱️ Test Time Analytics")
st.markdown("Performance optimization and test time analysis")

# Load data
@st.cache_data
def load_data():
    config = Config()
    sample_path = config.data_dir / 'sample' / 'sample_data.csv'
    staging_path = config.data_dir / 'staging' / 'test_results.parquet'
    
    if staging_path.exists():
        return pd.read_parquet(staging_path)
    elif sample_path.exists():
        return pd.read_csv(sample_path)
    else:
        return None

df = load_data()

if df is None:
    st.error("❌ No data available")
    st.stop()

# Initialize analytics
tta = TestTimeAnalytics(df)

# Overall Statistics
st.subheader("📊 Overall Statistics")
stats = tta.overall_statistics()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Average Test Time",
        f"{stats['avg_time_ms']:.1f} ms",
        delta=None
    )

with col2:
    st.metric(
        "Total Test Time",
        f"{stats['total_time_hours']:.1f} hours",
        delta=None
    )

with col3:
    st.metric(
        "Avg Device Time",
        f"{stats['avg_device_time_sec']:.1f} sec",
        delta=None
    )

with col4:
    st.metric(
        "Total Devices",
        f"{stats['total_devices']:,}",
        delta=None
    )

st.markdown("---")

# Test Time Distribution
st.subheader("📈 Test Time Distribution")

col1, col2 = st.columns([2, 1])

with col1:
    fig = tta.plot_test_time_distribution()
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### Statistics")
    st.markdown(f"- **Mean**: {stats['avg_time_ms']:.1f} ms")
    st.markdown(f"- **Median**: {stats['median_time_ms']:.1f} ms")
    st.markdown(f"- **Std Dev**: {stats['std_time_ms']:.1f} ms")
    st.markdown(f"- **Min**: {stats['min_time_ms']:.1f} ms")
    st.markdown(f"- **Max**: {stats['max_time_ms']:.1f} ms")

st.markdown("---")

# Test Time by Test
st.subheader("🧪 Time by Test")

col1, col2 = st.columns([2, 1])

with col1:
    fig = tta.plot_time_by_test(top_n=10)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    test_stats = tta.time_by_test().head(10)
    st.dataframe(
        test_stats[['test_name', 'mean', 'total', 'pct_total']].style.format({
            'mean': '{:.1f}',
            'total': '{:.0f}',
            'pct_total': '{:.1f}%'
        }),
        use_container_width=True,
        height=400
    )

st.markdown("---")

# Pareto Analysis
st.subheader("📉 Pareto Analysis: Time Contributors")

col1, col2 = st.columns([2, 1])

with col1:
    fig = tta.plot_pareto_chart(top_n=10)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    pareto = tta.pareto_test_time(top_n=10)
    st.dataframe(pareto, use_container_width=True, height=400)
    
    # 80/20 insight
    tests_for_80 = (pareto['cumulative_pct'] <= 80).sum()
    st.info(f"🎯 **80/20 Rule**: {tests_for_80} tests account for 80% of test time")

st.markdown("---")

# Pass vs Fail Time
st.subheader("🔍 Test Time: Pass vs Fail")

col1, col2 = st.columns([2, 1])

with col1:
    fig = tta.plot_time_by_result()
    st.plotly_chart(fig, use_container_width=True)

with col2:
    time_by_result = tta.time_by_result()
    st.markdown("#### Statistics")
    st.dataframe(time_by_result, use_container_width=True)
    
    # Statistical test
    from scipy import stats
    pass_times = df[df['result'] == 'pass']['test_time_ms']
    fail_times = df[df['result'] == 'fail']['test_time_ms']
    t_stat, p_value = stats.ttest_ind(pass_times, fail_times)
    
    if p_value < 0.05:
        st.warning(f"⚠️ Significant difference detected (p={p_value:.4f})")
    else:
        st.success(f"✅ No significant difference (p={p_value:.4f})")

st.markdown("---")

# Optimization Opportunities
st.subheader("💡 Optimization Opportunities")

opportunities = tta.optimization_opportunities()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### 🎯 High Contributors")
    if opportunities['high_contributors']:
        for test in opportunities['high_contributors']:
            st.markdown(f"- {test}")
    else:
        st.success("No tests contribute >10% of time")

with col2:
    st.markdown("#### 📊 High Variability")
    if opportunities['high_variability']:
        for test in opportunities['high_variability'][:5]:
            st.markdown(f"- {test}")
    else:
        st.success("All tests have consistent timing")

with col3:
    st.markdown("#### 🐢 Slowest Tests")
    for test in opportunities['slow_tests'][:5]:
        st.markdown(f"- {test}")

# Potential Savings
st.markdown("#### 💰 Potential Time Savings")

savings = opportunities['potential_savings']

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "If Top 3 Tests Reduced by 20%",
        f"{savings['top_3_reduction_20pct_ms'] / 1000:.1f} sec",
        delta=f"-{savings['top_3_reduction_20pct_pct']:.1f}%"
    )

with col2:
    st.metric(
        "If All Tests at 90th Percentile",
        f"{savings['all_at_p90_savings_ms'] / 1000:.1f} sec",
        delta=f"-{savings['all_at_p90_savings_pct']:.1f}%"
    )

st.markdown("---")

# Recommendations
st.subheader("🎯 Recommendations")

if opportunities['high_contributors']:
    st.warning(f"**High Priority**: {len(opportunities['high_contributors'])} tests contribute >10% of total time")
    st.markdown("**Action**: Focus optimization efforts on these tests first")

if opportunities['high_variability']:
    st.info(f"**Medium Priority**: {len(opportunities['high_variability'])} tests show high timing variability")
    st.markdown("**Action**: Investigate causes of inconsistent timing")

# Export
st.markdown("---")
st.subheader("📥 Export")

col1, col2 = st.columns(2)

with col1:
    if st.button("Export Test Time Summary"):
        csv = test_stats.to_csv(index=False)
        st.download_button("Download CSV", csv, "test_time_summary.csv", "text/csv")

with col2:
    if st.button("Export Pareto Analysis"):
        csv = pareto.to_csv(index=False)
        st.download_button("Download CSV", csv, "pareto_test_time.csv", "text/csv")
