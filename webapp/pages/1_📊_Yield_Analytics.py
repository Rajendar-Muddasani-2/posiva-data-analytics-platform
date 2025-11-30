"""
Yield Analytics Dashboard Page
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.analytics.yield_analytics import YieldAnalytics
from src.utils.config import Config

st.set_page_config(page_title="Yield Analytics", page_icon="📊", layout="wide")

# Header
st.title("📊 Yield Analytics")
st.markdown("Comprehensive yield analysis at device, test, lot, and wafer levels")

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
    st.error("❌ No data available. Please load data first.")
    st.stop()

# Initialize analytics
ya = YieldAnalytics(df)

# Sidebar filters
with st.sidebar:
    st.header("Filters")
    
    # Lot filter
    if 'lot_id' in df.columns:
        lots = ['All'] + list(df['lot_id'].unique())
        selected_lot = st.selectbox("Lot", lots)
        if selected_lot != 'All':
            df = df[df['lot_id'] == selected_lot]
            ya = YieldAnalytics(df)
    
    # Wafer filter
    if 'wafer_id' in df.columns:
        wafers = ['All'] + list(df['wafer_id'].unique())
        selected_wafer = st.selectbox("Wafer", wafers)
        if selected_wafer != 'All':
            df = df[df['wafer_id'] == selected_wafer]
            ya = YieldAnalytics(df)
    
    st.markdown("---")
    st.markdown(f"**Records**: {len(df):,}")
    st.markdown(f"**Devices**: {df['device_id'].nunique()}")

# Generate summary
summary = ya.generate_summary()

# Key Metrics
st.subheader("🎯 Key Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Overall Yield",
        f"{summary['overall_yield']:.2f}%",
        delta=f"{summary['overall_yield'] - 90:.2f}%" if summary['overall_yield'] >= 85 else None
    )

with col2:
    st.metric(
        "Passing Devices",
        f"{summary['passing_devices']:,}",
        delta=f"{summary['passing_devices']} / {summary['total_devices']}"
    )

with col3:
    st.metric(
        "Test Yield",
        f"{summary['test_yield']:.2f}%",
        delta=None
    )

with col4:
    st.metric(
        "Lowest Test",
        f"{summary['lowest_yield_value']:.1f}%",
        delta=summary['lowest_yield_test'],
        delta_color="off"
    )

st.markdown("---")

# Yield Trends
st.subheader("📈 Yield Trends")

col1, col2 = st.columns(2)

with col1:
    if 'lot_id' in df.columns:
        fig = ya.plot_yield_trend(by='lot')
        st.plotly_chart(fig, use_container_width=True)

with col2:
    if 'wafer_id' in df.columns:
        wafer_yield = ya.yield_by_wafer()
        if not wafer_yield.empty:
            fig = ya.plot_yield_trend(by='wafer')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Wafer data not available")

st.markdown("---")

# Test-Level Analysis
st.subheader("🧪 Test-Level Analysis")

col1, col2 = st.columns(2)

with col1:
    # Test yield table
    test_yield = ya.yield_by_test()
    st.dataframe(
        test_yield.style.background_gradient(cmap='RdYlGn', vmin=0, vmax=100),
        use_container_width=True,
        height=400
    )

with col2:
    # Test yield chart
    fig = px.bar(
        test_yield,
        x='test_name',
        y='yield',
        title='Yield by Test',
        labels={'yield': 'Yield (%)', 'test_name': 'Test'},
        text='yield',
        color='yield',
        color_continuous_scale='RdYlGn'
    )
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.add_hline(y=90, line_dash="dash", line_color="red", annotation_text="Target")
    fig.update_layout(xaxis_tickangle=45, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Pareto Analysis
st.subheader("📉 Pareto Analysis: Top Failing Tests")

col1, col2 = st.columns([2, 1])

with col1:
    fig = ya.plot_pareto(top_n=10)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    pareto_df = ya.failing_tests_pareto(top_n=10)
    st.dataframe(pareto_df, use_container_width=True, height=400)
    
    # 80/20 insight
    tests_for_80 = (pareto_df['cumulative_pct'] <= 80).sum()
    st.info(f"🎯 **Pareto Insight**: {tests_for_80} tests account for 80% of failures")

st.markdown("---")

# Yield Distribution
st.subheader("📊 Yield Distribution")

col1, col2 = st.columns([2, 1])

with col1:
    fig = ya.plot_yield_distribution()
    st.plotly_chart(fig, use_container_width=True)

with col2:
    device_pass_rate = df.groupby('device_id')['result'].apply(
        lambda x: (x == 'pass').sum() / len(x) * 100
    )
    
    st.markdown("#### Device Yield Buckets")
    st.markdown(f"- **100%**: {(device_pass_rate == 100).sum()} devices")
    st.markdown(f"- **90-99%**: {((device_pass_rate >= 90) & (device_pass_rate < 100)).sum()} devices")
    st.markdown(f"- **80-89%**: {((device_pass_rate >= 80) & (device_pass_rate < 90)).sum()} devices")
    st.markdown(f"- **<80%**: {(device_pass_rate < 80).sum()} devices")
    
    # Quality indicator
    if summary['overall_yield'] >= 95:
        st.success("✅ Excellent yield performance!")
    elif summary['overall_yield'] >= 90:
        st.warning("⚠️ Good, but room for improvement")
    else:
        st.error("❌ Yield needs attention")

st.markdown("---")

# Actionable Insights
st.subheader("💡 Actionable Insights")

test_yield_df = ya.yield_by_test()
low_yield_tests = test_yield_df[test_yield_df['yield'] < 90]

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 🎯 Priority Actions")
    if len(low_yield_tests) > 0:
        st.warning(f"**{len(low_yield_tests)} tests** below 90% yield target:")
        for _, row in low_yield_tests.iterrows():
            st.markdown(f"- **{row['test_name']}**: {row['yield']:.1f}%")
    else:
        st.success("✅ All tests meeting yield targets!")

with col2:
    st.markdown("#### 🔍 Focus Areas")
    top_failures = ya.failing_tests_pareto(top_n=3)
    st.markdown(f"Top 3 failure drivers account for **{top_failures['percentage'].sum():.1f}%** of all failures:")
    for _, row in top_failures.iterrows():
        st.markdown(f"- **{row['test_name']}**: {row['failures']} failures")

# Export options
st.markdown("---")
st.subheader("📥 Export")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Export Summary (CSV)"):
        summary_df = pd.DataFrame([summary])
        csv = summary_df.to_csv(index=False)
        st.download_button("Download", csv, "yield_summary.csv", "text/csv")

with col2:
    if st.button("Export Test Yield (CSV)"):
        csv = test_yield_df.to_csv(index=False)
        st.download_button("Download", csv, "test_yield.csv", "text/csv")

with col3:
    if st.button("Export Pareto (CSV)"):
        csv = pareto_df.to_csv(index=False)
        st.download_button("Download", csv, "pareto_analysis.csv", "text/csv")
