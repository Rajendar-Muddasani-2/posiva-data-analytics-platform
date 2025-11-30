"""
Parametric Analytics Dashboard Page

Displays parametric test analysis with Cpk, distributions, and outliers.
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analytics.parametric_analytics import ParametricAnalytics
from src.utils.config import Config

# Page configuration
st.set_page_config(
    page_title="Parametric Analytics - POSIVA",
    page_icon="📐",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .metric-value {
        font-size: 32px;
        font-weight: bold;
    }
    .metric-label {
        font-size: 14px;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("📐 Parametric Analytics")
st.markdown("Process capability analysis, distribution fitting, and outlier detection")

# Load data
@st.cache_data
def load_data():
    config = Config()
    sample_path = config.data_dir / 'sample' / 'sample_data.csv'
    if sample_path.exists():
        return pd.read_csv(sample_path)
    return None

df = load_data()

if df is None:
    st.error("❌ No data found. Please generate sample data first.")
    st.stop()

# Filter to parametric tests only
df_parametric = df[df['test_type'] == 'parametric'].copy()

if len(df_parametric) == 0:
    st.warning("No parametric test data available.")
    st.stop()

# Initialize analytics
pa = ParametricAnalytics(df_parametric)

# Sidebar filters
st.sidebar.header("Filters")

# Test selection
all_tests = sorted(df_parametric['test_name'].unique())
selected_test = st.sidebar.selectbox("Select Test", all_tests)

# Lot selection
all_lots = ['All'] + sorted(df_parametric['lot_id'].unique().tolist())
selected_lot = st.sidebar.selectbox("Select Lot", all_lots)

# Filter data
if selected_lot != 'All':
    df_filtered = df_parametric[
        (df_parametric['test_name'] == selected_test) & 
        (df_parametric['lot_id'] == selected_lot)
    ]
else:
    df_filtered = df_parametric[df_parametric['test_name'] == selected_test]

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Filtered Records:** {len(df_filtered)}")

# Main content
if len(df_filtered) == 0:
    st.warning("No data matches the selected filters.")
    st.stop()

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Cpk Analysis", "📈 Distributions", "🔍 Outliers", "🔗 Correlations"])

with tab1:
    st.header("Process Capability (Cpk)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Calculate Cpk
        cpk_results = pa.cpk_analysis(selected_test)
        
        if cpk_results is not None:
            # Display metrics
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{cpk_results["cpk"]:.3f}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Process Capability (Cpk)</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Interpretation
            cpk_val = cpk_results['cpk']
            if cpk_val >= 1.67:
                st.success("✅ Excellent capability (Cpk ≥ 1.67)")
            elif cpk_val >= 1.33:
                st.info("👍 Adequate capability (Cpk ≥ 1.33)")
            elif cpk_val >= 1.0:
                st.warning("⚠️ Marginal capability (Cpk ≥ 1.0)")
            else:
                st.error("🚨 Inadequate capability (Cpk < 1.0)")
            
            # Detailed metrics
            st.subheader("Capability Indices")
            metrics_df = pd.DataFrame({
                'Metric': ['Cp', 'Cpk', 'Cpu', 'Cpl', 'Mean', 'Std Dev'],
                'Value': [
                    f"{cpk_results['cp']:.3f}",
                    f"{cpk_results['cpk']:.3f}",
                    f"{cpk_results['cpu']:.3f}",
                    f"{cpk_results['cpl']:.3f}",
                    f"{cpk_results['mean']:.4f}",
                    f"{cpk_results['std']:.4f}"
                ]
            })
            st.dataframe(metrics_df, hide_index=True, use_container_width=True)
    
    with col2:
        # Plot distribution with limits
        if cpk_results is not None:
            fig = pa.plot_cpk(selected_test)
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("Distribution Analysis")
    
    # Fit distributions
    dist_results = pa.distribution_fit(selected_test)
    
    if dist_results is not None:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Best Fit Distribution")
            st.metric("Distribution", dist_results['best_fit'])
            st.metric("P-value (Normality)", f"{dist_results['normality_p_value']:.4f}")
            
            if dist_results['is_normal']:
                st.success("✅ Data follows normal distribution")
            else:
                st.warning("⚠️ Data is non-normal")
            
            st.markdown("**Distribution Parameters:**")
            for param, value in dist_results['params'].items():
                st.write(f"- {param}: {value:.4f}")
        
        with col2:
            # Plot distribution fit
            fig = pa.plot_distribution(selected_test)
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header("Outlier Detection")
    
    # Detect outliers
    outliers = pa.outlier_detection(selected_test, method='both')
    
    if outliers is not None:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Outliers", outliers['outlier_count'])
        with col2:
            st.metric("Outlier Rate", f"{outliers['outlier_rate']:.2f}%")
        with col3:
            st.metric("Detection Method", outliers['method'])
        
        # Show outlier details
        if outliers['outlier_count'] > 0:
            st.subheader("Outlier Details")
            outlier_df = df_filtered[df_filtered['device_id'].isin(outliers['outlier_devices'])]
            st.dataframe(
                outlier_df[['device_id', 'lot_id', 'wafer_id', 'measured_value', 'result']],
                hide_index=True,
                use_container_width=True
            )
            
            # Plot outliers
            fig = pa.plot_outliers(selected_test)
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("✅ No outliers detected")

with tab4:
    st.header("Correlation Analysis")
    
    # Calculate correlations
    corr_results = pa.correlation_analysis(threshold=0.5)
    
    if corr_results is not None and len(corr_results) > 0:
        st.subheader("Highly Correlated Test Pairs")
        st.markdown(f"*Showing correlations > 0.5 (found {len(corr_results)} pairs)*")
        
        corr_df = pd.DataFrame(corr_results)
        corr_df['correlation'] = corr_df['correlation'].apply(lambda x: f"{x:.3f}")
        
        st.dataframe(corr_df, hide_index=True, use_container_width=True)
        
        # Correlation heatmap
        fig = pa.plot_correlation_matrix()
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ℹ️ No strong correlations found (threshold: 0.5)")

# Insights section
st.markdown("---")
st.header("💡 Key Insights")

insights = []

# Cpk insight
cpk_results = pa.cpk_analysis(selected_test)
if cpk_results is not None:
    cpk_val = cpk_results['cpk']
    if cpk_val >= 1.67:
        insights.append(f"✅ {selected_test} has excellent process capability (Cpk = {cpk_val:.3f})")
    elif cpk_val < 1.0:
        insights.append(f"⚠️ {selected_test} requires process improvement (Cpk = {cpk_val:.3f})")

# Outlier insight
outliers = pa.outlier_detection(selected_test)
if outliers is not None and outliers['outlier_rate'] > 5:
    insights.append(f"🔍 High outlier rate detected: {outliers['outlier_rate']:.1f}% - Investigation recommended")

# Distribution insight
dist_results = pa.distribution_fit(selected_test)
if dist_results is not None and not dist_results['is_normal']:
    insights.append(f"📊 {selected_test} distribution is non-normal - Consider non-parametric methods")

if insights:
    for insight in insights:
        st.markdown(f"- {insight}")
else:
    st.success("✅ All parameters within acceptable ranges")

# Export options
st.markdown("---")
st.subheader("📥 Export Data")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Export Cpk Analysis"):
        cpk_results = pa.cpk_analysis(selected_test)
        if cpk_results:
            st.download_button(
                "Download CSV",
                pd.DataFrame([cpk_results]).to_csv(index=False),
                f"cpk_analysis_{selected_test}.csv",
                "text/csv"
            )

with col2:
    if st.button("Export Outliers"):
        outliers = pa.outlier_detection(selected_test)
        if outliers and outliers['outlier_count'] > 0:
            outlier_df = df_filtered[df_filtered['device_id'].isin(outliers['outlier_devices'])]
            st.download_button(
                "Download CSV",
                outlier_df.to_csv(index=False),
                f"outliers_{selected_test}.csv",
                "text/csv"
            )

with col3:
    if st.button("Export Filtered Data"):
        st.download_button(
            "Download CSV",
            df_filtered.to_csv(index=False),
            f"parametric_data_{selected_test}.csv",
            "text/csv"
        )
