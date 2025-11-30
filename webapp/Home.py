"""
POSIVA Analytics Dashboard - Main App
Streamlit multi-page application
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.utils.config import Config

# Page configuration
st.set_page_config(
    page_title="POSIVA Analytics Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stMetric {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize config
@st.cache_resource
def get_config():
    return Config()

config = get_config()

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/200x80/1f77b4/ffffff?text=POSIVA", use_container_width=True)
    st.title("Navigation")
    st.markdown("---")
    
    st.markdown("""
    ### 📊 Analytics Modules
    - **Home**: Overview & Quick Stats
    - **Yield Analytics**: Device & test yield analysis
    - **Test Time**: Performance optimization
    - **Parametric**: Measurement analysis
    - **Statistical**: Hypothesis testing & correlation
    
    ### 🤖 ML/AI Modules
    - **Predictions**: ML models
    - **Anomaly Detection**: Outliers
    - **Root Cause**: AI-powered RCA
    
    ### 📈 Reports
    - **Daily Summary**: Automated reports
    - **Custom Reports**: Build your own
    """)
    
    st.markdown("---")
    st.info(f"📂 Data: {config.data_dir.name}")

# Main content
st.markdown('<h1 class="main-header">📊 POSIVA Analytics Platform</h1>', unsafe_allow_html=True)

st.markdown("""
<div style="text-align: center; font-size: 1.2rem; color: #666; margin-bottom: 3rem;">
Advanced Analytics & AI for Semiconductor Post-Silicon Validation
</div>
""", unsafe_allow_html=True)

# Welcome section
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 🎯 What is POSIVA?
    
    POSIVA is an advanced analytics platform designed for semiconductor post-silicon validation. 
    It transforms raw test data into actionable insights using:
    
    - **Data Analytics**: Yield, test time, parametric analysis
    - **Statistical Methods**: Hypothesis testing, time series
    - **Machine Learning**: Predictions, clustering, anomaly detection
    - **AI-Powered Insights**: Automated RCA, natural language reports
    """)

with col2:
    st.markdown("""
    ### 📊 Key Features
    
    - **Interactive Dashboards**: Real-time visualizations
    - **Automated Reports**: Daily/weekly summaries
    - **ML Models**: Yield prediction, anomaly detection
    - **Statistical Analysis**: A/B testing, correlations
    - **Natural Language**: AI-generated insights
    - **Export Capability**: PDF, Excel, HTML reports
    """)

with col3:
    st.markdown("""
    ### 🚀 Quick Start
    
    1. **Load Data**: Upload STDF or CSV files
    2. **Explore**: Use analytics modules
    3. **Analyze**: Run statistical tests
    4. **Predict**: Apply ML models
    5. **Report**: Generate summaries
    
    👈 Use the sidebar to navigate between modules
    """)

st.markdown("---")

# Quick stats section
st.subheader("📈 Quick Statistics")

try:
    import pandas as pd
    sample_data_path = config.data_dir / 'sample' / 'sample_data.csv'
    
    if sample_data_path.exists():
        df = pd.read_csv(sample_data_path)
        
        # Calculate metrics
        total_devices = df['device_id'].nunique()
        total_tests = len(df)
        overall_yield = (df['result'] == 'pass').sum() / len(df) * 100
        avg_test_time = df['test_time_ms'].mean()
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Devices",
                value=f"{total_devices:,}",
                delta=None
            )
        
        with col2:
            st.metric(
                label="Total Tests",
                value=f"{total_tests:,}",
                delta=None
            )
        
        with col3:
            st.metric(
                label="Overall Yield",
                value=f"{overall_yield:.1f}%",
                delta=f"{overall_yield - 90:.1f}%" if overall_yield >= 90 else None,
                delta_color="normal" if overall_yield >= 90 else "inverse"
            )
        
        with col4:
            st.metric(
                label="Avg Test Time",
                value=f"{avg_test_time:.1f} ms",
                delta=None
            )
        
        # Quick chart
        st.markdown("#### 📊 Test Result Distribution")
        result_counts = df['result'].value_counts()
        
        chart_col1, chart_col2 = st.columns([2, 1])
        
        with chart_col1:
            import plotly.express as px
            fig = px.pie(
                values=result_counts.values,
                names=result_counts.index,
                title='Pass/Fail Distribution',
                color=result_counts.index,
                color_discrete_map={'pass': '#2ecc71', 'fail': '#e74c3c'}
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        with chart_col2:
            st.markdown("##### Key Insights")
            st.markdown(f"""
            - ✅ **Pass**: {result_counts.get('pass', 0):,} ({result_counts.get('pass', 0)/len(df)*100:.1f}%)
            - ❌ **Fail**: {result_counts.get('fail', 0):,} ({result_counts.get('fail', 0)/len(df)*100:.1f}%)
            - 📊 **Yield**: {"🟢 Good" if overall_yield >= 90 else "🟡 Needs Improvement"}
            - 🎯 **Target**: 90%+
            """)
    
    else:
        st.info("📂 No data loaded yet. Please upload data or use sample data generation.")
        
        if st.button("Generate Sample Data"):
            with st.spinner("Generating sample data..."):
                import subprocess
                result = subprocess.run(
                    ["python3", str(project_root / "scripts" / "generate_sample_data.py")],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    st.success("✅ Sample data generated! Refresh the page.")
                else:
                    st.error(f"Error: {result.stderr}")

except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.info("Generate sample data using the button above or upload your own data.")

st.markdown("---")

# Footer
st.markdown("""
<div style="text-align: center; color: #666; margin-top: 3rem;">
    <p>POSIVA Analytics Platform v1.0.0</p>
    <p>Built with ❤️ using Streamlit, Plotly, scikit-learn, and TensorFlow</p>
</div>
""", unsafe_allow_html=True)
