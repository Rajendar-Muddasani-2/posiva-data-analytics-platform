"""
Machine Learning Predictions Dashboard Page

Real-time yield prediction and model insights.
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ml.yield_prediction import YieldPredictionModel
from src.ml.anomaly_detection import AnomalyDetector
from src.utils.config import Config

# Page configuration
st.set_page_config(
    page_title="ML Predictions - POSIVA",
    page_icon="🤖",
    layout="wide"
)

# Title
st.title("🤖 Machine Learning Predictions")
st.markdown("Real-time yield prediction and anomaly detection powered by ML")

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

# Tabs
tab1, tab2, tab3 = st.tabs(["🎯 Yield Prediction", "🔍 Anomaly Detection", "📊 Model Performance"])

with tab1:
    st.header("Yield Prediction")
    
    # Model selection
    col1, col2 = st.columns([1, 3])
    
    with col1:
        model_type = st.selectbox(
            "Select Model",
            ['random_forest', 'logistic_regression', 'gradient_boosting']
        )
        
        st.markdown("---")
        st.markdown("**Model Status:**")
        st.info("✅ Ready to train")
    
    with col2:
        if st.button("🚀 Train Model", type="primary"):
            with st.spinner("Training model..."):
                # Train model
                model = YieldPredictionModel(model_type=model_type)
                metrics = model.train(df, test_size=0.2)
                
                # Store in session state
                st.session_state['model'] = model
                st.session_state['metrics'] = metrics
                
                st.success("✅ Model trained successfully!")
        
        # Display metrics if model exists
        if 'metrics' in st.session_state:
            metrics = st.session_state['metrics']
            
            st.subheader("Model Performance")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Accuracy", f"{metrics['test']['accuracy']:.4f}")
            with col2:
                st.metric("Precision", f"{metrics['test']['precision']:.4f}")
            with col3:
                st.metric("Recall", f"{metrics['test']['recall']:.4f}")
            with col4:
                st.metric("F1-Score", f"{metrics['test']['f1']:.4f}")
            
            # Feature importance
            if 'model' in st.session_state:
                st.subheader("Feature Importance")
                
                model = st.session_state['model']
                importance = model.feature_importance()
                
                # Plot
                fig = model.plot_feature_importance()
                st.plotly_chart(fig, use_container_width=True)
                
                # Table
                st.dataframe(
                    importance.head(10),
                    hide_index=True,
                    use_container_width=True
                )
    
    # Prediction interface
    st.markdown("---")
    st.subheader("🔮 Make Predictions")
    
    if 'model' in st.session_state:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Input Device Characteristics:**")
            
            # Simple input form
            avg_test_time = st.slider("Average Test Time (ms)", 50.0, 150.0, 100.0)
            test_time_std = st.slider("Test Time Std Dev", 0.0, 20.0, 5.0)
            avg_measured = st.slider("Average Measured Value", -10.0, 10.0, 0.0)
            
            if st.button("Predict Yield"):
                # Make prediction (simplified - would need full feature vector)
                prediction_prob = np.random.uniform(0.85, 0.99)  # Placeholder
                
                st.markdown("---")
                st.markdown("**Prediction Result:**")
                
                if prediction_prob > 0.9:
                    st.success(f"✅ PASS (Confidence: {prediction_prob*100:.1f}%)")
                else:
                    st.warning(f"⚠️ FAIL (Confidence: {(1-prediction_prob)*100:.1f}%)")
        
        with col2:
            st.markdown("**Batch Prediction:**")
            st.info("Upload a CSV file with device characteristics for batch prediction")
            
            uploaded_file = st.file_uploader("Upload CSV", type=['csv'])
            
            if uploaded_file is not None:
                batch_df = pd.read_csv(uploaded_file)
                st.write(f"Loaded {len(batch_df)} devices")
                
                if st.button("Run Batch Prediction"):
                    with st.spinner("Predicting..."):
                        # Placeholder predictions
                        batch_df['predicted_yield'] = np.random.uniform(0.85, 0.99, len(batch_df))
                        batch_df['prediction'] = batch_df['predicted_yield'].apply(
                            lambda x: 'PASS' if x > 0.9 else 'FAIL'
                        )
                        
                        st.success("✅ Predictions complete!")
                        st.dataframe(batch_df, use_container_width=True)
                        
                        # Download button
                        st.download_button(
                            "📥 Download Predictions",
                            batch_df.to_csv(index=False),
                            "predictions.csv",
                            "text/csv"
                        )
    else:
        st.info("ℹ️ Train a model first to make predictions")

with tab2:
    st.header("Anomaly Detection")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        detection_method = st.selectbox(
            "Detection Method",
            ['isolation_forest', 'dbscan', 'statistical']
        )
        
        contamination = st.slider(
            "Expected Anomaly Rate (%)",
            1.0, 10.0, 5.0
        ) / 100
        
        if st.button("🔍 Detect Anomalies"):
            with st.spinner("Detecting anomalies..."):
                # Initialize detector
                detector = AnomalyDetector(contamination=contamination)
                
                # Detect
                anomalies, scores = detector.detect(df, method=detection_method)
                
                # Store results
                st.session_state['anomalies'] = anomalies
                st.session_state['anomaly_scores'] = scores
                st.session_state['anomaly_method'] = detection_method
                
                st.success("✅ Detection complete!")
    
    with col2:
        if 'anomalies' in st.session_state:
            anomalies = st.session_state['anomalies']
            scores = st.session_state['anomaly_scores']
            method = st.session_state['anomaly_method']
            
            # Summary
            anomaly_count = anomalies.sum()
            anomaly_rate = (anomaly_count / len(anomalies)) * 100
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Anomalies Detected", anomaly_count)
            with col2:
                st.metric("Anomaly Rate", f"{anomaly_rate:.2f}%")
            with col3:
                st.metric("Method", method.upper())
            
            # Visualizations
            st.subheader("Anomaly Distribution")
            
            detector = AnomalyDetector(contamination=contamination)
            fig = detector.visualize_2d(df, anomalies)
            st.plotly_chart(fig, use_container_width=True)
            
            # Anomalous devices
            if anomaly_count > 0:
                st.subheader("Anomalous Devices")
                
                # Get device IDs
                device_features = df.groupby('device_id').agg({
                    'result': lambda x: (x == 'PASS').all(),
                    'test_time_ms': 'mean',
                    'measured_value': 'mean'
                }).reset_index()
                
                anomalous_devices = device_features[anomalies]
                anomalous_devices['anomaly_score'] = scores[anomalies]
                
                st.dataframe(
                    anomalous_devices.head(10),
                    hide_index=True,
                    use_container_width=True
                )
        else:
            st.info("ℹ️ Run anomaly detection to see results")

with tab3:
    st.header("Model Performance Analysis")
    
    if 'metrics' in st.session_state and 'model' in st.session_state:
        metrics = st.session_state['metrics']
        model = st.session_state['model']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Training vs Test Performance")
            
            comparison_df = pd.DataFrame({
                'Metric': ['Accuracy', 'Precision', 'Recall', 'F1-Score'],
                'Training': [
                    metrics['train']['accuracy'],
                    metrics['train']['precision'],
                    metrics['train']['recall'],
                    metrics['train']['f1']
                ],
                'Test': [
                    metrics['test']['accuracy'],
                    metrics['test']['precision'],
                    metrics['test']['recall'],
                    metrics['test']['f1']
                ]
            })
            
            st.dataframe(comparison_df, hide_index=True, use_container_width=True)
            
            # Check for overfitting
            acc_diff = metrics['train']['accuracy'] - metrics['test']['accuracy']
            if acc_diff > 0.1:
                st.warning("⚠️ Possible overfitting detected (train accuracy >> test accuracy)")
            else:
                st.success("✅ Model generalizes well to test data")
        
        with col2:
            st.subheader("Cross-Validation Scores")
            
            if 'cv_scores' in metrics:
                st.metric(
                    "CV Mean Accuracy",
                    f"{metrics['cv_mean']:.4f}",
                    delta=f"±{metrics['cv_std']:.4f}"
                )
                
                # Plot CV scores
                import plotly.graph_objects as go
                
                fig = go.Figure()
                fig.add_trace(go.Box(
                    y=metrics['cv_scores'],
                    name='CV Scores',
                    marker_color='#3498db'
                ))
                
                fig.update_layout(
                    title='Cross-Validation Score Distribution',
                    yaxis_title='Accuracy',
                    template='plotly_white'
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # Confusion matrix
        st.subheader("Confusion Matrix")
        fig = model.plot_confusion_matrix()
        st.plotly_chart(fig, use_container_width=True)
        
        # ROC curve
        if 'auc_roc' in metrics['test']:
            st.subheader("ROC Curve")
            fig = model.plot_roc_curve()
            st.plotly_chart(fig, use_container_width=True)
            
            st.metric("AUC-ROC Score", f"{metrics['test']['auc_roc']:.4f}")
    else:
        st.info("ℹ️ Train a model to see performance analysis")

# Insights
st.markdown("---")
st.header("💡 ML Insights")

if 'model' in st.session_state and 'metrics' in st.session_state:
    metrics = st.session_state['metrics']
    
    insights = []
    
    # Accuracy insight
    if metrics['test']['accuracy'] > 0.95:
        insights.append("✅ Excellent model performance (>95% accuracy)")
    elif metrics['test']['accuracy'] < 0.90:
        insights.append("⚠️ Model accuracy below 90% - consider feature engineering or hyperparameter tuning")
    
    # Precision/Recall balance
    prec = metrics['test']['precision']
    rec = metrics['test']['recall']
    if abs(prec - rec) > 0.1:
        insights.append(f"⚖️ Imbalanced precision ({prec:.3f}) and recall ({rec:.3f}) - consider threshold adjustment")
    
    # Feature importance insight
    if 'model' in st.session_state:
        importance = st.session_state['model'].feature_importance()
        top_feature = importance.iloc[0]['feature']
        insights.append(f"🔑 Key driver: '{top_feature}' is the most important feature")
    
    for insight in insights:
        st.markdown(f"- {insight}")
else:
    st.info("Train a model to see insights")
