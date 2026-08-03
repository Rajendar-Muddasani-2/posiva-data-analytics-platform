"""
Anomaly Detection Module
Unsupervised learning for outlier and anomaly detection
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Optional, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import plotly.graph_objects as go
import plotly.express as px
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AnomalyDetector:
    """
    Anomaly detection using multiple methods
    """
    
    def __init__(self, method: str = 'isolation_forest'):
        """
        Initialize anomaly detector
        
        Args:
            method: 'isolation_forest', 'dbscan', or 'statistical'
        """
        self.method = method
        self.model = None
        self.scaler = StandardScaler()
        self.pca = None
        self.logger = logger
        
        if method == 'isolation_forest':
            self.model = IsolationForest(contamination=0.05, random_state=42)
        elif method == 'dbscan':
            self.model = DBSCAN(eps=0.5, min_samples=5)
        elif method == 'statistical':
            pass  # No model needed
        else:
            raise ValueError(f"Unknown method: {method}")
        
        self.logger.info(f"Initialized {method} anomaly detector")
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Prepare features for anomaly detection
        
        Args:
            df: Input DataFrame
            
        Returns:
            Original dataframe with device IDs, feature matrix
        """
        # Aggregate to device level
        device_features = []
        
        for device_id in df['device_id'].unique():
            device_data = df[df['device_id'] == device_id]
            
            features = {
                'device_id': device_id,
                'total_tests': len(device_data),
                'pass_rate': (device_data['result'] == 'pass').sum() / len(device_data),
                'total_test_time': device_data['test_time_ms'].sum(),
                'avg_test_time': device_data['test_time_ms'].mean(),
                'std_test_time': device_data['test_time_ms'].std(),
                'max_test_time': device_data['test_time_ms'].max(),
                'min_test_time': device_data['test_time_ms'].min(),
            }
            
            # Test-specific pass rates
            for test_name in device_data['test_name'].unique():
                test_data = device_data[device_data['test_name'] == test_name]
                features[f'{test_name}_pass'] = (test_data['result'] == 'pass').sum()
            
            # Parametric features
            if 'measured_value' in device_data.columns:
                parametric = device_data[device_data['measured_value'].notna()]
                if len(parametric) > 0:
                    features['avg_measured_value'] = parametric['measured_value'].mean()
                    features['std_measured_value'] = parametric['measured_value'].std()
            
            device_features.append(features)
        
        features_df = pd.DataFrame(device_features)
        
        # Keep device_id separate
        device_ids = features_df[['device_id']].copy()
        X = features_df.drop('device_id', axis=1)
        
        # Fill NaN
        X = X.fillna(X.mean())
        
        return device_ids, X
    
    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect anomalies
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with anomaly labels
        """
        device_ids, X = self.prepare_features(df)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        if self.method == 'isolation_forest':
            # Fit and predict (-1 for anomaly, 1 for normal)
            predictions = self.model.fit_predict(X_scaled)
            anomaly_scores = self.model.score_samples(X_scaled)
            
            device_ids['anomaly'] = (predictions == -1).astype(int)
            device_ids['anomaly_score'] = -anomaly_scores  # Invert for intuitive interpretation
        
        elif self.method == 'dbscan':
            # Fit (-1 for outliers)
            labels = self.model.fit_predict(X_scaled)
            
            device_ids['anomaly'] = (labels == -1).astype(int)
            device_ids['cluster'] = labels
        
        elif self.method == 'statistical':
            # Z-score method
            z_scores = np.abs(stats.zscore(X_scaled, axis=0))
            max_z_scores = z_scores.max(axis=1)
            
            device_ids['anomaly'] = (max_z_scores > 3).astype(int)
            device_ids['anomaly_score'] = max_z_scores
        
        # Merge with original data
        result = df.merge(device_ids, on='device_id')
        
        self.logger.info(f"Detected {device_ids['anomaly'].sum()} anomalies out of {len(device_ids)} devices")
        
        return result
    
    def get_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        """Get only anomalous devices"""
        result = self.detect(df)
        anomalies = result[result['anomaly'] == 1]
        
        return anomalies
    
    def visualize_2d(self, df: pd.DataFrame) -> go.Figure:
        """Visualize anomalies in 2D using PCA"""
        device_ids, X = self.prepare_features(df)
        X_scaled = self.scaler.fit_transform(X)
        
        # Apply PCA for visualization
        self.pca = PCA(n_components=2)
        X_pca = self.pca.fit_transform(X_scaled)
        
        # Detect anomalies
        if self.method == 'isolation_forest':
            predictions = self.model.fit_predict(X_scaled)
            anomaly_labels = ['Anomaly' if p == -1 else 'Normal' for p in predictions]
        elif self.method == 'dbscan':
            labels = self.model.fit_predict(X_scaled)
            anomaly_labels = ['Anomaly' if l == -1 else f'Cluster {l}' for l in labels]
        else:
            z_scores = np.abs(stats.zscore(X_scaled, axis=0))
            max_z_scores = z_scores.max(axis=1)
            anomaly_labels = ['Anomaly' if z > 3 else 'Normal' for z in max_z_scores]
        
        # Create plot
        plot_df = pd.DataFrame({
            'PC1': X_pca[:, 0],
            'PC2': X_pca[:, 1],
            'Label': anomaly_labels,
            'Device': device_ids['device_id']
        })
        
        fig = px.scatter(
            plot_df,
            x='PC1',
            y='PC2',
            color='Label',
            title='Anomaly Detection (PCA Visualization)',
            hover_data=['Device'],
            color_discrete_map={'Anomaly': 'red', 'Normal': 'blue'}
        )
        
        fig.update_layout(template='plotly_white')
        
        return fig
    
    def analyze_anomalies(self, df: pd.DataFrame) -> Dict:
        """Analyze characteristics of detected anomalies"""
        result = self.detect(df)
        
        normal = result[result['anomaly'] == 0]
        anomalous = result[result['anomaly'] == 1]
        
        analysis = {
            'total_devices': df['device_id'].nunique(),
            'normal_devices': normal['device_id'].nunique(),
            'anomalous_devices': anomalous['device_id'].nunique(),
            'anomaly_rate': float(anomalous['device_id'].nunique() / df['device_id'].nunique()),
        }
        
        # Compare characteristics
        if len(anomalous) > 0:
            analysis['anomaly_characteristics'] = {
                'avg_test_time': float(anomalous.groupby('device_id')['test_time_ms'].sum().mean()),
                'pass_rate': float((anomalous['result'] == 'pass').sum() / len(anomalous)),
                'failing_tests': anomalous[anomalous['result'] == 'fail']['test_name'].value_counts().to_dict()
            }
            
            analysis['normal_characteristics'] = {
                'avg_test_time': float(normal.groupby('device_id')['test_time_ms'].sum().mean()),
                'pass_rate': float((normal['result'] == 'pass').sum() / len(normal))
            }
        
        return analysis


class ClusterAnalyzer:
    """
    Clustering analysis for pattern discovery
    """
    
    def __init__(self, n_clusters: int = 3):
        """
        Initialize cluster analyzer
        
        Args:
            n_clusters: Number of clusters
        """
        from sklearn.cluster import KMeans
        
        self.n_clusters = n_clusters
        self.model = KMeans(n_clusters=n_clusters, random_state=42)
        self.scaler = StandardScaler()
        self.pca = None
        self.logger = logger
    
    def cluster(self, df: pd.DataFrame) -> pd.DataFrame:
        """Perform clustering"""
        # Use same feature preparation as anomaly detector
        detector = AnomalyDetector()
        device_ids, X = detector.prepare_features(df)
        
        # Scale and cluster
        X_scaled = self.scaler.fit_transform(X)
        cluster_labels = self.model.fit_predict(X_scaled)
        
        device_ids['cluster'] = cluster_labels
        
        # Merge with original data
        result = df.merge(device_ids, on='device_id')
        
        self.logger.info(f"Clustered devices into {self.n_clusters} groups")
        
        return result
    
    def visualize_clusters(self, df: pd.DataFrame) -> go.Figure:
        """Visualize clusters in 2D"""
        detector = AnomalyDetector()
        device_ids, X = detector.prepare_features(df)
        
        X_scaled = self.scaler.fit_transform(X)
        cluster_labels = self.model.fit_predict(X_scaled)
        
        # PCA for visualization
        self.pca = PCA(n_components=2)
        X_pca = self.pca.fit_transform(X_scaled)
        
        plot_df = pd.DataFrame({
            'PC1': X_pca[:, 0],
            'PC2': X_pca[:, 1],
            'Cluster': cluster_labels.astype(str),
            'Device': device_ids['device_id']
        })
        
        fig = px.scatter(
            plot_df,
            x='PC1',
            y='PC2',
            color='Cluster',
            title=f'Device Clustering (k={self.n_clusters})',
            hover_data=['Device']
        )
        
        fig.update_layout(template='plotly_white')
        
        return fig
