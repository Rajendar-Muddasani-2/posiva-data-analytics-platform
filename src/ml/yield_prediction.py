"""
Machine Learning - Yield Prediction Models
Supervised learning for yield prediction and classification
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import confusion_matrix, classification_report, roc_auc_score, roc_curve
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import joblib
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)


class YieldPredictionModel:
    """
    Machine learning models for yield prediction
    """
    
    def __init__(self, model_type: str = 'random_forest'):
        """
        Initialize yield prediction model
        
        Args:
            model_type: 'logistic', 'random_forest', or 'gradient_boosting'
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.label_encoder = LabelEncoder()
        self.metrics = {}
        self.logger = logger
        
        # Initialize model
        if model_type == 'logistic':
            self.model = LogisticRegression(random_state=42, max_iter=1000)
        elif model_type == 'random_forest':
            self.model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        elif model_type == 'gradient_boosting':
            self.model = GradientBoostingClassifier(n_estimators=100, random_state=42)
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        self.logger.info(f"Initialized {model_type} model")
    
    def prepare_features(self, df: pd.DataFrame, target_col: str = 'result') -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare features for training
        
        Args:
            df: Input DataFrame
            target_col: Target column name
            
        Returns:
            X (features), y (target)
        """
        # Feature engineering
        feature_df = df.copy()
        
        # Aggregate to device level
        device_features = []
        
        for device_id in feature_df['device_id'].unique():
            device_data = feature_df[feature_df['device_id'] == device_id]
            
            features = {
                'device_id': device_id,
                'total_tests': len(device_data),
                'total_test_time': device_data['test_time_ms'].sum(),
                'avg_test_time': device_data['test_time_ms'].mean(),
                'max_test_time': device_data['test_time_ms'].max(),
                'min_test_time': device_data['test_time_ms'].min(),
                'std_test_time': device_data['test_time_ms'].std(),
            }
            
            # Parametric features
            if 'measured_value' in device_data.columns:
                parametric = device_data[device_data['measured_value'].notna()]
                if len(parametric) > 0:
                    features['avg_measured_value'] = parametric['measured_value'].mean()
                    features['std_measured_value'] = parametric['measured_value'].std()
                    features['min_measured_value'] = parametric['measured_value'].min()
                    features['max_measured_value'] = parametric['measured_value'].max()
            
            # Bin
            if 'bin' in device_data.columns:
                features['bin'] = device_data['bin'].iloc[0]
            
            # Target: device passes if all tests pass
            features['device_pass'] = 1 if (device_data['result'] == 'pass').all() else 0
            
            device_features.append(features)
        
        features_df = pd.DataFrame(device_features)
        
        # Fill NaN values
        features_df = features_df.fillna(features_df.mean(numeric_only=True))
        
        # Separate features and target
        X = features_df.drop(['device_id', 'device_pass'], axis=1, errors='ignore')
        y = features_df['device_pass']
        
        self.feature_names = list(X.columns)
        
        return X, y
    
    def train(self, df: pd.DataFrame, test_size: float = 0.2) -> Dict:
        """
        Train the model
        
        Args:
            df: Training DataFrame
            test_size: Test set proportion
            
        Returns:
            Dictionary with training metrics
        """
        self.logger.info("Preparing features...")
        X, y = self.prepare_features(df)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.logger.info(f"Training {self.model_type} model...")
        self.model.fit(X_train_scaled, y_train)
        
        # Predictions
        y_pred_train = self.model.predict(X_train_scaled)
        y_pred_test = self.model.predict(X_test_scaled)
        
        # Probabilities (if available)
        if hasattr(self.model, 'predict_proba'):
            y_prob_test = self.model.predict_proba(X_test_scaled)[:, 1]
        else:
            y_prob_test = None
        
        # Calculate metrics
        train_metrics = {
            'accuracy': accuracy_score(y_train, y_pred_train),
            'precision': precision_score(y_train, y_pred_train, zero_division=0),
            'recall': recall_score(y_train, y_pred_train, zero_division=0),
            'f1': f1_score(y_train, y_pred_train, zero_division=0)
        }
        
        test_metrics = {
            'accuracy': accuracy_score(y_test, y_pred_test),
            'precision': precision_score(y_test, y_pred_test, zero_division=0),
            'recall': recall_score(y_test, y_pred_test, zero_division=0),
            'f1': f1_score(y_test, y_pred_test, zero_division=0)
        }
        
        if y_prob_test is not None:
            test_metrics['auc_roc'] = roc_auc_score(y_test, y_prob_test)
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5)
        
        self.metrics = {
            'train': train_metrics,
            'test': test_metrics,
            'cv_mean': float(cv_scores.mean()),
            'cv_std': float(cv_scores.std()),
            'n_train': len(X_train),
            'n_test': len(X_test),
            'features': self.feature_names
        }
        
        self.logger.info(f"Training complete. Test accuracy: {test_metrics['accuracy']:.4f}")
        
        return self.metrics
    
    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """
        Make predictions on new data
        
        Args:
            df: Input DataFrame
            
        Returns:
            Predictions array
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        X, _ = self.prepare_features(df)
        X_scaled = self.scaler.transform(X)
        
        predictions = self.model.predict(X_scaled)
        
        return predictions
    
    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        """
        Predict probabilities
        
        Args:
            df: Input DataFrame
            
        Returns:
            Probability array
        """
        if self.model is None:
            raise ValueError("Model not trained")
        
        if not hasattr(self.model, 'predict_proba'):
            raise ValueError("Model doesn't support probability prediction")
        
        X, _ = self.prepare_features(df)
        X_scaled = self.scaler.transform(X)
        
        probabilities = self.model.predict_proba(X_scaled)
        
        return probabilities
    
    def feature_importance(self) -> pd.DataFrame:
        """Get feature importance (for tree-based models)"""
        if not hasattr(self.model, 'feature_importances_'):
            raise ValueError("Model doesn't support feature importance")
        
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        return importance_df
    
    def plot_confusion_matrix(self, df: pd.DataFrame) -> go.Figure:
        """Plot confusion matrix"""
        X, y = self.prepare_features(df)
        X_scaled = self.scaler.transform(X)
        y_pred = self.model.predict(X_scaled)
        
        cm = confusion_matrix(y, y_pred)
        
        fig = px.imshow(
            cm,
            labels=dict(x="Predicted", y="Actual", color="Count"),
            x=['Fail', 'Pass'],
            y=['Fail', 'Pass'],
            title='Confusion Matrix',
            text_auto=True,
            color_continuous_scale='Blues'
        )
        
        return fig
    
    def plot_roc_curve(self, df: pd.DataFrame) -> go.Figure:
        """Plot ROC curve"""
        if not hasattr(self.model, 'predict_proba'):
            raise ValueError("Model doesn't support probability prediction")
        
        X, y = self.prepare_features(df)
        X_scaled = self.scaler.transform(X)
        y_prob = self.model.predict_proba(X_scaled)[:, 1]
        
        fpr, tpr, _ = roc_curve(y, y_prob)
        auc = roc_auc_score(y, y_prob)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=fpr, y=tpr,
            name=f'ROC Curve (AUC = {auc:.3f})',
            mode='lines',
            line=dict(color='blue', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=[0, 1], y=[0, 1],
            name='Random',
            mode='lines',
            line=dict(color='gray', dash='dash')
        ))
        
        fig.update_layout(
            title='ROC Curve',
            xaxis_title='False Positive Rate',
            yaxis_title='True Positive Rate',
            template='plotly_white'
        )
        
        return fig
    
    def plot_feature_importance(self, top_n: int = 10) -> go.Figure:
        """Plot feature importance"""
        importance_df = self.feature_importance().head(top_n)
        
        fig = px.bar(
            importance_df,
            x='importance',
            y='feature',
            orientation='h',
            title=f'Top {top_n} Feature Importance',
            labels={'importance': 'Importance', 'feature': 'Feature'}
        )
        
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        
        return fig
    
    def save_model(self, path: Path):
        """Save model to disk"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'model_type': self.model_type,
            'metrics': self.metrics
        }
        
        joblib.dump(model_data, path)
        self.logger.info(f"Model saved to {path}")
    
    @classmethod
    def load_model(cls, path: Path):
        """Load model from disk"""
        model_data = joblib.load(path)
        
        instance = cls(model_type=model_data['model_type'])
        instance.model = model_data['model']
        instance.scaler = model_data['scaler']
        instance.feature_names = model_data['feature_names']
        instance.metrics = model_data['metrics']
        
        logger.info(f"Model loaded from {path}")
        
        return instance
