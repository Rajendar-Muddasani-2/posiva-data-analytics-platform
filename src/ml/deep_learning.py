"""
Deep Learning Module for Semiconductor Analytics

This module provides deep learning capabilities for:
- Neural networks for yield prediction
- LSTM for time series forecasting
- Autoencoders for anomaly detection
- Feature learning and embeddings

Author: POSIVA Analytics Team
Date: 2024
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
import logging
from pathlib import Path

# TensorFlow and Keras
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models, callbacks
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import BinaryCrossentropy, MeanSquaredError
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

# Visualization
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)


class NeuralYieldPredictor:
    """
    Deep Neural Network for Yield Prediction
    
    Multi-layer feedforward network for binary classification (PASS/FAIL)
    with advanced features like batch normalization and dropout.
    """
    
    def __init__(self, input_dim: int, hidden_layers: List[int] = [64, 32, 16],
                 dropout_rate: float = 0.3, learning_rate: float = 0.001):
        """
        Initialize neural network predictor
        
        Args:
            input_dim: Number of input features
            hidden_layers: List of hidden layer sizes
            dropout_rate: Dropout rate for regularization
            learning_rate: Learning rate for optimizer
        """
        self.input_dim = input_dim
        self.hidden_layers = hidden_layers
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        
        self.model = None
        self.scaler = StandardScaler()
        self.history = None
        self.feature_names = None
        
    def build_model(self) -> keras.Model:
        """
        Build deep neural network architecture
        
        Returns:
            Compiled Keras model
        """
        model = models.Sequential(name='YieldPredictor')
        
        # Input layer
        model.add(layers.Input(shape=(self.input_dim,), name='input'))
        
        # Hidden layers with batch normalization and dropout
        for i, units in enumerate(self.hidden_layers):
            model.add(layers.Dense(
                units, 
                activation='relu',
                kernel_initializer='he_normal',
                name=f'dense_{i+1}'
            ))
            model.add(layers.BatchNormalization(name=f'bn_{i+1}'))
            model.add(layers.Dropout(self.dropout_rate, name=f'dropout_{i+1}'))
        
        # Output layer (binary classification)
        model.add(layers.Dense(1, activation='sigmoid', name='output'))
        
        # Compile model
        model.compile(
            optimizer=Adam(learning_rate=self.learning_rate),
            loss=BinaryCrossentropy(),
            metrics=['accuracy', 
                    keras.metrics.Precision(name='precision'),
                    keras.metrics.Recall(name='recall'),
                    keras.metrics.AUC(name='auc')]
        )
        
        return model
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare features for neural network
        
        Args:
            df: Input dataframe with test results
            
        Returns:
            Tuple of (X, y) arrays
        """
        # Device-level aggregation
        device_features = df.groupby('device_id').agg({
            'result': lambda x: (x == 'PASS').all(),  # Target
            'test_time_ms': ['mean', 'std', 'min', 'max'],
            'measured_value': ['mean', 'std', 'min', 'max'],
            'test_num': 'count'
        }).reset_index()
        
        # Flatten column names
        device_features.columns = ['_'.join(col).strip('_') for col in device_features.columns]
        device_features.rename(columns={'result_<lambda>': 'pass'}, inplace=True)
        
        # Extract features and target
        feature_cols = [col for col in device_features.columns if col not in ['device_id', 'pass']]
        self.feature_names = feature_cols
        
        X = device_features[feature_cols].values
        y = device_features['pass'].astype(int).values
        
        return X, y
    
    def train(self, df: pd.DataFrame, epochs: int = 100, batch_size: int = 32,
             validation_split: float = 0.2, early_stopping: bool = True,
             patience: int = 10) -> Dict:
        """
        Train neural network
        
        Args:
            df: Training dataframe
            epochs: Number of training epochs
            batch_size: Batch size for training
            validation_split: Fraction of data for validation
            early_stopping: Enable early stopping
            patience: Patience for early stopping
            
        Returns:
            Dictionary with training history and metrics
        """
        # Prepare data
        X, y = self.prepare_features(df)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Build model
        self.model = self.build_model()
        
        logger.info("Model architecture:")
        logger.info(self.model.summary())
        
        # Callbacks
        callback_list = []
        
        if early_stopping:
            early_stop = callbacks.EarlyStopping(
                monitor='val_loss',
                patience=patience,
                restore_best_weights=True,
                verbose=1
            )
            callback_list.append(early_stop)
        
        # Reduce learning rate on plateau
        reduce_lr = callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=1e-6,
            verbose=1
        )
        callback_list.append(reduce_lr)
        
        # Train model
        history = self.model.fit(
            X_train_scaled, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=callback_list,
            verbose=1
        )
        
        self.history = history
        
        # Evaluate on test set
        y_pred_proba = self.model.predict(X_test_scaled, verbose=0).flatten()
        y_pred = (y_pred_proba > 0.5).astype(int)
        
        metrics = {
            'train': {
                'loss': float(history.history['loss'][-1]),
                'accuracy': float(history.history['accuracy'][-1])
            },
            'test': {
                'accuracy': float(accuracy_score(y_test, y_pred)),
                'precision': float(precision_score(y_test, y_pred, zero_division=0)),
                'recall': float(recall_score(y_test, y_pred, zero_division=0)),
                'f1': float(f1_score(y_test, y_pred, zero_division=0)),
                'auc_roc': float(roc_auc_score(y_test, y_pred_proba))
            },
            'epochs_trained': len(history.history['loss'])
        }
        
        logger.info(f"Training complete: {metrics['epochs_trained']} epochs")
        logger.info(f"Test Accuracy: {metrics['test']['accuracy']:.4f}")
        
        return metrics
    
    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """Predict yield for devices"""
        X, _ = self.prepare_features(df)
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled, verbose=0).flatten()
        return predictions
    
    def plot_training_history(self) -> go.Figure:
        """Plot training history"""
        if self.history is None:
            raise ValueError("No training history available")
        
        history = self.history.history
        epochs = range(1, len(history['loss']) + 1)
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Loss', 'Accuracy', 'Precision', 'Recall')
        )
        
        # Loss
        fig.add_trace(go.Scatter(x=list(epochs), y=history['loss'], name='Train Loss'), row=1, col=1)
        fig.add_trace(go.Scatter(x=list(epochs), y=history['val_loss'], name='Val Loss'), row=1, col=1)
        
        # Accuracy
        fig.add_trace(go.Scatter(x=list(epochs), y=history['accuracy'], name='Train Acc'), row=1, col=2)
        fig.add_trace(go.Scatter(x=list(epochs), y=history['val_accuracy'], name='Val Acc'), row=1, col=2)
        
        # Precision
        fig.add_trace(go.Scatter(x=list(epochs), y=history['precision'], name='Train Prec'), row=2, col=1)
        fig.add_trace(go.Scatter(x=list(epochs), y=history['val_precision'], name='Val Prec'), row=2, col=1)
        
        # Recall
        fig.add_trace(go.Scatter(x=list(epochs), y=history['recall'], name='Train Rec'), row=2, col=2)
        fig.add_trace(go.Scatter(x=list(epochs), y=history['val_recall'], name='Val Rec'), row=2, col=2)
        
        fig.update_xaxes(title_text="Epoch")
        fig.update_layout(height=700, showlegend=True, title_text="Training History")
        
        return fig
    
    def save(self, path: str) -> None:
        """Save model and scaler"""
        self.model.save(path)
        import joblib
        joblib.dump(self.scaler, f"{path}_scaler.pkl")
        logger.info(f"Model saved to {path}")
    
    def load(self, path: str) -> None:
        """Load model and scaler"""
        self.model = keras.models.load_model(path)
        import joblib
        self.scaler = joblib.load(f"{path}_scaler.pkl")
        logger.info(f"Model loaded from {path}")


class LSTMForecaster:
    """
    LSTM (Long Short-Term Memory) for Time Series Forecasting
    
    Recurrent neural network for sequence prediction with memory cells.
    Ideal for time series with long-term dependencies.
    """
    
    def __init__(self, lstm_units: List[int] = [64, 32], 
                 dropout_rate: float = 0.2,
                 learning_rate: float = 0.001):
        """
        Initialize LSTM forecaster
        
        Args:
            lstm_units: List of LSTM layer sizes
            dropout_rate: Dropout rate for regularization
            learning_rate: Learning rate for optimizer
        """
        self.lstm_units = lstm_units
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        
        self.model = None
        self.scaler = MinMaxScaler()
        self.history = None
        self.lookback = None
        
    def create_sequences(self, data: np.ndarray, lookback: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sequences for LSTM training
        
        Args:
            data: Input time series data
            lookback: Number of time steps to look back
            
        Returns:
            Tuple of (X, y) sequences
        """
        X, y = [], []
        
        for i in range(len(data) - lookback):
            X.append(data[i:(i + lookback)])
            y.append(data[i + lookback])
        
        return np.array(X), np.array(y)
    
    def build_model(self, input_shape: Tuple[int, int]) -> keras.Model:
        """
        Build LSTM architecture
        
        Args:
            input_shape: (lookback, features)
            
        Returns:
            Compiled Keras model
        """
        model = models.Sequential(name='LSTM_Forecaster')
        
        # LSTM layers
        for i, units in enumerate(self.lstm_units):
            return_sequences = (i < len(self.lstm_units) - 1)
            
            model.add(layers.LSTM(
                units,
                return_sequences=return_sequences,
                dropout=self.dropout_rate,
                recurrent_dropout=self.dropout_rate,
                name=f'lstm_{i+1}'
            ))
        
        # Output layer
        model.add(layers.Dense(1, name='output'))
        
        # Compile
        model.compile(
            optimizer=Adam(learning_rate=self.learning_rate),
            loss=MeanSquaredError(),
            metrics=['mae', 'mse']
        )
        
        return model
    
    def train(self, series: pd.Series, lookback: int = 14, epochs: int = 100,
             batch_size: int = 32, validation_split: float = 0.2) -> Dict:
        """
        Train LSTM model
        
        Args:
            series: Time series data
            lookback: Number of past time steps to use
            epochs: Number of training epochs
            batch_size: Batch size for training
            validation_split: Fraction of data for validation
            
        Returns:
            Dictionary with training metrics
        """
        self.lookback = lookback
        
        # Scale data
        data_scaled = self.scaler.fit_transform(series.values.reshape(-1, 1)).flatten()
        
        # Create sequences
        X, y = self.create_sequences(data_scaled, lookback)
        
        # Reshape for LSTM [samples, time steps, features]
        X = X.reshape((X.shape[0], X.shape[1], 1))
        
        # Split data
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Build model
        self.model = self.build_model(input_shape=(lookback, 1))
        
        logger.info("LSTM Model architecture:")
        logger.info(self.model.summary())
        
        # Callbacks
        early_stop = callbacks.EarlyStopping(
            monitor='val_loss',
            patience=15,
            restore_best_weights=True
        )
        
        # Train
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=[early_stop],
            verbose=1
        )
        
        self.history = history
        
        # Evaluate
        y_pred = self.model.predict(X_test, verbose=0).flatten()
        
        # Inverse transform for metrics
        y_test_orig = self.scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()
        y_pred_orig = self.scaler.inverse_transform(y_pred.reshape(-1, 1)).flatten()
        
        mae = np.mean(np.abs(y_test_orig - y_pred_orig))
        rmse = np.sqrt(np.mean((y_test_orig - y_pred_orig) ** 2))
        
        metrics = {
            'epochs_trained': len(history.history['loss']),
            'test_mae': float(mae),
            'test_rmse': float(rmse)
        }
        
        logger.info(f"Training complete: {metrics['epochs_trained']} epochs")
        logger.info(f"Test RMSE: {metrics['test_rmse']:.4f}")
        
        return metrics
    
    def forecast(self, series: pd.Series, steps: int) -> np.ndarray:
        """
        Forecast future values
        
        Args:
            series: Historical time series
            steps: Number of steps to forecast
            
        Returns:
            Array of forecasted values
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Scale data
        data_scaled = self.scaler.transform(series.values.reshape(-1, 1)).flatten()
        
        # Use last lookback points as initial sequence
        current_sequence = data_scaled[-self.lookback:].reshape(1, self.lookback, 1)
        
        forecasts = []
        
        for _ in range(steps):
            # Predict next value
            next_pred = self.model.predict(current_sequence, verbose=0)[0, 0]
            forecasts.append(next_pred)
            
            # Update sequence (shift and append prediction)
            current_sequence = np.roll(current_sequence, -1, axis=1)
            current_sequence[0, -1, 0] = next_pred
        
        # Inverse transform
        forecasts = self.scaler.inverse_transform(np.array(forecasts).reshape(-1, 1)).flatten()
        
        return forecasts
    
    def plot_forecast(self, series: pd.Series, steps: int = 30) -> go.Figure:
        """Plot historical data and forecast"""
        forecast = self.forecast(series, steps)
        
        # Create future dates
        last_date = series.index[-1]
        future_dates = pd.date_range(start=last_date, periods=steps+1, freq='D')[1:]
        
        fig = go.Figure()
        
        # Historical
        fig.add_trace(go.Scatter(
            x=series.index,
            y=series.values,
            mode='lines',
            name='Historical',
            line=dict(color='#3498db', width=2)
        ))
        
        # Forecast
        fig.add_trace(go.Scatter(
            x=future_dates,
            y=forecast,
            mode='lines+markers',
            name='Forecast',
            line=dict(color='#e74c3c', width=2, dash='dash')
        ))
        
        fig.update_layout(
            title='LSTM Time Series Forecast',
            xaxis_title='Date',
            yaxis_title='Value',
            hovermode='x unified',
            template='plotly_white'
        )
        
        return fig


class Autoencoder:
    """
    Autoencoder for Anomaly Detection
    
    Neural network that learns to compress and reconstruct normal patterns.
    Anomalies have high reconstruction error.
    """
    
    def __init__(self, input_dim: int, encoding_dim: int = 8,
                 hidden_layers: List[int] = [32, 16],
                 learning_rate: float = 0.001):
        """
        Initialize autoencoder
        
        Args:
            input_dim: Number of input features
            encoding_dim: Dimension of encoded representation (bottleneck)
            hidden_layers: Hidden layer sizes for encoder/decoder
            learning_rate: Learning rate for optimizer
        """
        self.input_dim = input_dim
        self.encoding_dim = encoding_dim
        self.hidden_layers = hidden_layers
        self.learning_rate = learning_rate
        
        self.model = None
        self.scaler = StandardScaler()
        self.threshold = None
        
    def build_model(self) -> keras.Model:
        """
        Build autoencoder architecture
        
        Returns:
            Compiled Keras model
        """
        # Input
        input_layer = layers.Input(shape=(self.input_dim,), name='input')
        
        # Encoder
        encoded = input_layer
        for i, units in enumerate(self.hidden_layers):
            encoded = layers.Dense(units, activation='relu', name=f'encoder_{i+1}')(encoded)
        
        # Bottleneck (encoding)
        encoded = layers.Dense(self.encoding_dim, activation='relu', name='bottleneck')(encoded)
        
        # Decoder
        decoded = encoded
        for i, units in enumerate(reversed(self.hidden_layers)):
            decoded = layers.Dense(units, activation='relu', name=f'decoder_{i+1}')(decoded)
        
        # Output (reconstruction)
        decoded = layers.Dense(self.input_dim, activation='linear', name='output')(decoded)
        
        # Model
        autoencoder = models.Model(input_layer, decoded, name='Autoencoder')
        
        # Compile
        autoencoder.compile(
            optimizer=Adam(learning_rate=self.learning_rate),
            loss=MeanSquaredError(),
            metrics=['mae']
        )
        
        return autoencoder
    
    def train(self, X_normal: np.ndarray, epochs: int = 100, batch_size: int = 32,
             validation_split: float = 0.2, contamination: float = 0.05) -> Dict:
        """
        Train autoencoder on normal data
        
        Args:
            X_normal: Normal data (no anomalies)
            epochs: Number of training epochs
            batch_size: Batch size for training
            validation_split: Fraction of data for validation
            contamination: Expected fraction of anomalies (for threshold)
            
        Returns:
            Dictionary with training metrics
        """
        # Scale data
        X_scaled = self.scaler.fit_transform(X_normal)
        
        # Build model
        self.model = self.build_model()
        
        logger.info("Autoencoder architecture:")
        logger.info(self.model.summary())
        
        # Callbacks
        early_stop = callbacks.EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        )
        
        # Train (input = output for autoencoder)
        history = self.model.fit(
            X_scaled, X_scaled,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=[early_stop],
            verbose=1
        )
        
        # Calculate reconstruction errors on training data
        X_reconstructed = self.model.predict(X_scaled, verbose=0)
        reconstruction_errors = np.mean((X_scaled - X_reconstructed) ** 2, axis=1)
        
        # Set threshold at contamination percentile
        self.threshold = float(np.percentile(reconstruction_errors, (1 - contamination) * 100))
        
        metrics = {
            'epochs_trained': len(history.history['loss']),
            'final_loss': float(history.history['loss'][-1]),
            'threshold': self.threshold,
            'mean_reconstruction_error': float(np.mean(reconstruction_errors))
        }
        
        logger.info(f"Training complete: {metrics['epochs_trained']} epochs")
        logger.info(f"Anomaly threshold: {self.threshold:.6f}")
        
        return metrics
    
    def detect_anomalies(self, X: np.ndarray) -> Dict:
        """
        Detect anomalies based on reconstruction error
        
        Args:
            X: Data to check for anomalies
            
        Returns:
            Dictionary with anomaly predictions and scores
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Scale
        X_scaled = self.scaler.transform(X)
        
        # Reconstruct
        X_reconstructed = self.model.predict(X_scaled, verbose=0)
        
        # Calculate reconstruction errors
        reconstruction_errors = np.mean((X_scaled - X_reconstructed) ** 2, axis=1)
        
        # Detect anomalies
        is_anomaly = reconstruction_errors > self.threshold
        
        return {
            'is_anomaly': is_anomaly,
            'anomaly_score': reconstruction_errors,
            'threshold': self.threshold,
            'num_anomalies': int(np.sum(is_anomaly)),
            'anomaly_rate': float(np.mean(is_anomaly))
        }
    
    def plot_reconstruction_error(self, X: np.ndarray) -> go.Figure:
        """Plot reconstruction error distribution"""
        results = self.detect_anomalies(X)
        
        fig = go.Figure()
        
        # Histogram of reconstruction errors
        fig.add_trace(go.Histogram(
            x=results['anomaly_score'],
            name='Reconstruction Error',
            nbinsx=50,
            marker=dict(color='#3498db')
        ))
        
        # Threshold line
        fig.add_vline(
            x=self.threshold,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Threshold: {self.threshold:.6f}"
        )
        
        fig.update_layout(
            title='Reconstruction Error Distribution (Anomaly Detection)',
            xaxis_title='Reconstruction Error',
            yaxis_title='Count',
            template='plotly_white'
        )
        
        return fig


if __name__ == "__main__":
    print("Deep Learning Module for Semiconductor Analytics")
    print("=" * 60)
    print("✅ TensorFlow version:", tf.__version__)
    print("✅ GPU available:", len(tf.config.list_physical_devices('GPU')) > 0)
    print("\nAvailable models:")
    print("  1. NeuralYieldPredictor - Deep NN for yield prediction")
    print("  2. LSTMForecaster - LSTM for time series forecasting")
    print("  3. Autoencoder - Anomaly detection via reconstruction error")
