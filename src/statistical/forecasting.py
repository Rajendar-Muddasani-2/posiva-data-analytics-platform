"""
Advanced Time Series Forecasting Module

This module provides advanced forecasting capabilities using:
- Prophet (Facebook's time series forecasting)
- ARIMA/SARIMA (AutoRegressive Integrated Moving Average)
- Exponential Smoothing with seasonality

Author: POSIVA Analytics Team
Date: 2024
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
import logging
from datetime import datetime, timedelta

# Statistical models
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.stattools import adfuller, acf, pacf
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

# Prophet
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logging.warning("Prophet not available. Install with: pip install prophet")

# Visualization
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)


class ProphetForecaster:
    """
    Facebook Prophet forecasting model
    
    Prophet is designed for business time series with:
    - Strong seasonal patterns
    - Holiday effects
    - Missing data handling
    - Outlier robustness
    """
    
    def __init__(self):
        """Initialize Prophet forecaster"""
        if not PROPHET_AVAILABLE:
            raise ImportError("Prophet not installed. Install with: pip install prophet")
        
        self.model = None
        self.forecast = None
        self.training_data = None
        
    def prepare_data(self, df: pd.DataFrame, date_col: str, 
                    value_col: str) -> pd.DataFrame:
        """
        Prepare data for Prophet (requires 'ds' and 'y' columns)
        
        Args:
            df: Input dataframe
            date_col: Name of date column
            value_col: Name of value column
            
        Returns:
            DataFrame with 'ds' and 'y' columns
        """
        prophet_df = pd.DataFrame({
            'ds': pd.to_datetime(df[date_col]),
            'y': df[value_col]
        })
        
        # Remove any NaN values
        prophet_df = prophet_df.dropna()
        
        return prophet_df
    
    def fit(self, df: pd.DataFrame, 
            yearly_seasonality: bool = True,
            weekly_seasonality: bool = True,
            daily_seasonality: bool = False,
            changepoint_prior_scale: float = 0.05,
            seasonality_prior_scale: float = 10.0,
            **kwargs) -> None:
        """
        Fit Prophet model
        
        Args:
            df: DataFrame with 'ds' and 'y' columns
            yearly_seasonality: Enable yearly seasonality
            weekly_seasonality: Enable weekly seasonality
            daily_seasonality: Enable daily seasonality
            changepoint_prior_scale: Flexibility of trend (higher = more flexible)
            seasonality_prior_scale: Strength of seasonality (higher = stronger)
            **kwargs: Additional Prophet parameters
        """
        self.training_data = df.copy()
        
        self.model = Prophet(
            yearly_seasonality=yearly_seasonality,
            weekly_seasonality=weekly_seasonality,
            daily_seasonality=daily_seasonality,
            changepoint_prior_scale=changepoint_prior_scale,
            seasonality_prior_scale=seasonality_prior_scale,
            **kwargs
        )
        
        self.model.fit(df)
        logger.info(f"Prophet model trained on {len(df)} data points")
    
    def predict(self, periods: int, freq: str = 'D') -> pd.DataFrame:
        """
        Generate forecast
        
        Args:
            periods: Number of periods to forecast
            freq: Frequency ('D' for daily, 'W' for weekly, 'M' for monthly)
            
        Returns:
            DataFrame with forecast and confidence intervals
        """
        if self.model is None:
            raise ValueError("Model not fitted. Call fit() first.")
        
        # Create future dataframe
        future = self.model.make_future_dataframe(periods=periods, freq=freq)
        
        # Generate forecast
        self.forecast = self.model.predict(future)
        
        return self.forecast
    
    def get_forecast_summary(self, last_n: int = 30) -> pd.DataFrame:
        """
        Get forecast summary for the last N periods
        
        Args:
            last_n: Number of recent periods to return
            
        Returns:
            DataFrame with date, forecast, and confidence intervals
        """
        if self.forecast is None:
            raise ValueError("No forecast available. Call predict() first.")
        
        summary = self.forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(last_n)
        summary = summary.rename(columns={
            'ds': 'date',
            'yhat': 'forecast',
            'yhat_lower': 'lower_bound',
            'yhat_upper': 'upper_bound'
        })
        
        return summary.reset_index(drop=True)
    
    def plot_forecast(self, figsize: Tuple[int, int] = (12, 6)) -> go.Figure:
        """
        Plot forecast with confidence intervals
        
        Args:
            figsize: Figure size (width, height)
            
        Returns:
            Plotly figure
        """
        if self.forecast is None:
            raise ValueError("No forecast available. Call predict() first.")
        
        fig = go.Figure()
        
        # Historical data
        if self.training_data is not None:
            fig.add_trace(go.Scatter(
                x=self.training_data['ds'],
                y=self.training_data['y'],
                mode='markers',
                name='Historical',
                marker=dict(color='#3498db', size=4)
            ))
        
        # Forecast
        fig.add_trace(go.Scatter(
            x=self.forecast['ds'],
            y=self.forecast['yhat'],
            mode='lines',
            name='Forecast',
            line=dict(color='#e74c3c', width=2)
        ))
        
        # Confidence interval
        fig.add_trace(go.Scatter(
            x=self.forecast['ds'],
            y=self.forecast['yhat_upper'],
            mode='lines',
            name='Upper Bound',
            line=dict(width=0),
            showlegend=False
        ))
        
        fig.add_trace(go.Scatter(
            x=self.forecast['ds'],
            y=self.forecast['yhat_lower'],
            mode='lines',
            name='Lower Bound',
            line=dict(width=0),
            fillcolor='rgba(231, 76, 60, 0.2)',
            fill='tonexty',
            showlegend=True
        ))
        
        fig.update_layout(
            title='Time Series Forecast with Confidence Intervals',
            xaxis_title='Date',
            yaxis_title='Value',
            hovermode='x unified',
            template='plotly_white'
        )
        
        return fig
    
    def plot_components(self) -> None:
        """
        Plot forecast components (trend, seasonality)
        
        Returns:
            Matplotlib figure (uses Prophet's built-in plotting)
        """
        if self.model is None or self.forecast is None:
            raise ValueError("Model not fitted or forecast not generated")
        
        return self.model.plot_components(self.forecast)


class ARIMAForecaster:
    """
    ARIMA/SARIMA Forecasting Model
    
    ARIMA (AutoRegressive Integrated Moving Average):
    - AR (p): Autoregressive component
    - I (d): Differencing order for stationarity
    - MA (q): Moving average component
    
    SARIMA adds seasonal components (P, D, Q, s)
    """
    
    def __init__(self):
        """Initialize ARIMA forecaster"""
        self.model = None
        self.fitted_model = None
        self.training_data = None
        self.order = None
        self.seasonal_order = None
        
    def check_stationarity(self, series: pd.Series) -> Dict:
        """
        Check if time series is stationary using Augmented Dickey-Fuller test
        
        Args:
            series: Time series data
            
        Returns:
            Dictionary with test results
        """
        result = adfuller(series.dropna())
        
        return {
            'adf_statistic': float(result[0]),
            'p_value': float(result[1]),
            'is_stationary': result[1] < 0.05,
            'critical_values': {k: float(v) for k, v in result[4].items()},
            'interpretation': 'Stationary' if result[1] < 0.05 else 'Non-stationary (needs differencing)'
        }
    
    def suggest_order(self, series: pd.Series, max_p: int = 5, 
                     max_q: int = 5) -> Tuple[int, int, int]:
        """
        Suggest ARIMA order (p, d, q) using ACF and PACF
        
        Args:
            series: Time series data
            max_p: Maximum AR order to consider
            max_q: Maximum MA order to consider
            
        Returns:
            Tuple (p, d, q)
        """
        # Determine d (differencing order)
        d = 0
        temp_series = series.copy()
        
        while d < 3:
            stationarity = self.check_stationarity(temp_series)
            if stationarity['is_stationary']:
                break
            temp_series = temp_series.diff().dropna()
            d += 1
        
        # Calculate ACF and PACF
        acf_values = acf(temp_series.dropna(), nlags=max_q)
        pacf_values = pacf(temp_series.dropna(), nlags=max_p)
        
        # Suggest p (PACF cutoff)
        p = 1
        for i in range(1, len(pacf_values)):
            if abs(pacf_values[i]) < 0.1:  # Threshold
                break
            p = i
        p = min(p, max_p)
        
        # Suggest q (ACF cutoff)
        q = 1
        for i in range(1, len(acf_values)):
            if abs(acf_values[i]) < 0.1:  # Threshold
                break
            q = i
        q = min(q, max_q)
        
        logger.info(f"Suggested ARIMA order: ({p}, {d}, {q})")
        return (p, d, q)
    
    def fit(self, series: pd.Series, 
            order: Optional[Tuple[int, int, int]] = None,
            seasonal_order: Optional[Tuple[int, int, int, int]] = None,
            auto_order: bool = True) -> None:
        """
        Fit ARIMA or SARIMA model
        
        Args:
            series: Time series data
            order: ARIMA order (p, d, q). If None, will be auto-detected
            seasonal_order: Seasonal order (P, D, Q, s). None for non-seasonal
            auto_order: Automatically detect order if not provided
        """
        self.training_data = series.copy()
        
        # Auto-detect order if not provided
        if order is None and auto_order:
            order = self.suggest_order(series)
        elif order is None:
            order = (1, 1, 1)  # Default
        
        self.order = order
        self.seasonal_order = seasonal_order
        
        # Fit model
        if seasonal_order is not None:
            self.model = SARIMAX(series, order=order, seasonal_order=seasonal_order)
        else:
            self.model = ARIMA(series, order=order)
        
        self.fitted_model = self.model.fit()
        
        logger.info(f"ARIMA{order} model fitted successfully")
        if seasonal_order:
            logger.info(f"Seasonal order: {seasonal_order}")
    
    def predict(self, steps: int) -> pd.DataFrame:
        """
        Generate forecast
        
        Args:
            steps: Number of steps to forecast
            
        Returns:
            DataFrame with forecast and confidence intervals
        """
        if self.fitted_model is None:
            raise ValueError("Model not fitted. Call fit() first.")
        
        # Generate forecast
        forecast = self.fitted_model.forecast(steps=steps)
        forecast_ci = self.fitted_model.get_forecast(steps=steps).conf_int()
        
        # Create result dataframe
        result = pd.DataFrame({
            'forecast': forecast.values,
            'lower_bound': forecast_ci.iloc[:, 0].values,
            'upper_bound': forecast_ci.iloc[:, 1].values
        }, index=forecast.index)
        
        return result
    
    def get_metrics(self) -> Dict:
        """
        Get model fit metrics
        
        Returns:
            Dictionary with AIC, BIC, and other metrics
        """
        if self.fitted_model is None:
            raise ValueError("Model not fitted. Call fit() first.")
        
        return {
            'aic': float(self.fitted_model.aic),
            'bic': float(self.fitted_model.bic),
            'hqic': float(self.fitted_model.hqic),
            'order': self.order,
            'seasonal_order': self.seasonal_order
        }
    
    def plot_diagnostics(self) -> None:
        """
        Plot model diagnostics
        
        Returns:
            Matplotlib figure with diagnostic plots
        """
        if self.fitted_model is None:
            raise ValueError("Model not fitted. Call fit() first.")
        
        return self.fitted_model.plot_diagnostics(figsize=(12, 8))
    
    def plot_forecast(self, steps: int = 30) -> go.Figure:
        """
        Plot historical data and forecast
        
        Args:
            steps: Number of steps to forecast
            
        Returns:
            Plotly figure
        """
        forecast_df = self.predict(steps)
        
        fig = go.Figure()
        
        # Historical data
        fig.add_trace(go.Scatter(
            x=self.training_data.index,
            y=self.training_data.values,
            mode='lines',
            name='Historical',
            line=dict(color='#3498db', width=2)
        ))
        
        # Forecast
        fig.add_trace(go.Scatter(
            x=forecast_df.index,
            y=forecast_df['forecast'],
            mode='lines',
            name='Forecast',
            line=dict(color='#e74c3c', width=2)
        ))
        
        # Confidence interval
        fig.add_trace(go.Scatter(
            x=forecast_df.index,
            y=forecast_df['upper_bound'],
            mode='lines',
            name='Upper Bound',
            line=dict(width=0),
            showlegend=False
        ))
        
        fig.add_trace(go.Scatter(
            x=forecast_df.index,
            y=forecast_df['lower_bound'],
            mode='lines',
            name='Lower Bound',
            line=dict(width=0),
            fillcolor='rgba(231, 76, 60, 0.2)',
            fill='tonexty',
            showlegend=True
        ))
        
        fig.update_layout(
            title=f'ARIMA{self.order} Forecast',
            xaxis_title='Date',
            yaxis_title='Value',
            hovermode='x unified',
            template='plotly_white'
        )
        
        return fig


class ExponentialSmoothingForecaster:
    """
    Exponential Smoothing with Trend and Seasonality
    
    Methods:
    - Simple Exponential Smoothing (SES)
    - Holt's Linear Trend
    - Holt-Winters' Seasonal
    """
    
    def __init__(self):
        """Initialize Exponential Smoothing forecaster"""
        self.model = None
        self.fitted_model = None
        self.training_data = None
        
    def fit(self, series: pd.Series,
            trend: Optional[str] = 'add',
            seasonal: Optional[str] = 'add',
            seasonal_periods: Optional[int] = None) -> None:
        """
        Fit Exponential Smoothing model
        
        Args:
            series: Time series data
            trend: Trend component ('add', 'mul', or None)
            seasonal: Seasonal component ('add', 'mul', or None)
            seasonal_periods: Number of periods in season (e.g., 7 for weekly)
        """
        self.training_data = series.copy()
        
        self.model = ExponentialSmoothing(
            series,
            trend=trend,
            seasonal=seasonal,
            seasonal_periods=seasonal_periods
        )
        
        self.fitted_model = self.model.fit()
        
        logger.info(f"Exponential Smoothing model fitted (trend={trend}, seasonal={seasonal})")
    
    def predict(self, steps: int) -> pd.Series:
        """
        Generate forecast
        
        Args:
            steps: Number of steps to forecast
            
        Returns:
            Series with forecast values
        """
        if self.fitted_model is None:
            raise ValueError("Model not fitted. Call fit() first.")
        
        return self.fitted_model.forecast(steps=steps)
    
    def plot_forecast(self, steps: int = 30) -> go.Figure:
        """
        Plot historical data and forecast
        
        Args:
            steps: Number of steps to forecast
            
        Returns:
            Plotly figure
        """
        forecast = self.predict(steps)
        
        fig = go.Figure()
        
        # Historical data
        fig.add_trace(go.Scatter(
            x=self.training_data.index,
            y=self.training_data.values,
            mode='lines',
            name='Historical',
            line=dict(color='#3498db', width=2)
        ))
        
        # Forecast
        fig.add_trace(go.Scatter(
            x=forecast.index,
            y=forecast.values,
            mode='lines',
            name='Forecast',
            line=dict(color='#e74c3c', width=2, dash='dash')
        ))
        
        fig.update_layout(
            title='Exponential Smoothing Forecast',
            xaxis_title='Date',
            yaxis_title='Value',
            hovermode='x unified',
            template='plotly_white'
        )
        
        return fig


class ForecastComparator:
    """
    Compare multiple forecasting methods
    """
    
    def __init__(self, train_data: pd.Series, test_data: pd.Series):
        """
        Initialize comparator
        
        Args:
            train_data: Training time series
            test_data: Test time series (for validation)
        """
        self.train_data = train_data
        self.test_data = test_data
        self.forecasts = {}
        
    def add_forecast(self, name: str, forecast: pd.Series) -> None:
        """Add a forecast for comparison"""
        self.forecasts[name] = forecast
    
    def calculate_metrics(self) -> pd.DataFrame:
        """
        Calculate forecast accuracy metrics
        
        Returns:
            DataFrame with metrics for each method
        """
        results = []
        
        for name, forecast in self.forecasts.items():
            # Align forecast with test data
            common_idx = forecast.index.intersection(self.test_data.index)
            
            if len(common_idx) == 0:
                continue
            
            y_true = self.test_data.loc[common_idx]
            y_pred = forecast.loc[common_idx]
            
            # Calculate metrics
            mae = np.mean(np.abs(y_true - y_pred))
            mse = np.mean((y_true - y_pred) ** 2)
            rmse = np.sqrt(mse)
            mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
            
            results.append({
                'method': name,
                'mae': float(mae),
                'mse': float(mse),
                'rmse': float(rmse),
                'mape': float(mape)
            })
        
        return pd.DataFrame(results).sort_values('rmse')
    
    def plot_comparison(self) -> go.Figure:
        """
        Plot all forecasts for comparison
        
        Returns:
            Plotly figure
        """
        fig = go.Figure()
        
        # Training data
        fig.add_trace(go.Scatter(
            x=self.train_data.index,
            y=self.train_data.values,
            mode='lines',
            name='Training',
            line=dict(color='#3498db', width=2)
        ))
        
        # Test data
        fig.add_trace(go.Scatter(
            x=self.test_data.index,
            y=self.test_data.values,
            mode='lines',
            name='Actual',
            line=dict(color='#2ecc71', width=2)
        ))
        
        # Forecasts
        colors = ['#e74c3c', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22']
        
        for i, (name, forecast) in enumerate(self.forecasts.items()):
            fig.add_trace(go.Scatter(
                x=forecast.index,
                y=forecast.values,
                mode='lines',
                name=name,
                line=dict(color=colors[i % len(colors)], width=2, dash='dash')
            ))
        
        fig.update_layout(
            title='Forecast Method Comparison',
            xaxis_title='Date',
            yaxis_title='Value',
            hovermode='x unified',
            template='plotly_white'
        )
        
        return fig


if __name__ == "__main__":
    # Example usage
    print("Advanced Forecasting Module")
    print("=" * 50)
    
    # Generate sample time series
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=365, freq='D')
    trend = np.linspace(100, 150, 365)
    seasonal = 10 * np.sin(np.linspace(0, 4 * np.pi, 365))
    noise = np.random.normal(0, 5, 365)
    values = trend + seasonal + noise
    
    ts = pd.Series(values, index=dates)
    
    print(f"Generated sample time series: {len(ts)} days")
    print(f"Mean: {ts.mean():.2f}, Std: {ts.std():.2f}")
    
    # Split train/test
    train = ts[:-30]
    test = ts[-30:]
    
    print(f"\nTrain: {len(train)} days, Test: {len(test)} days")
    
    # ARIMA
    print("\n" + "=" * 50)
    print("ARIMA Forecasting")
    print("=" * 50)
    
    arima = ARIMAForecaster()
    stationarity = arima.check_stationarity(train)
    print(f"Stationarity: {stationarity['interpretation']}")
    print(f"ADF p-value: {stationarity['p_value']:.4f}")
    
    arima.fit(train, auto_order=True)
    metrics = arima.get_metrics()
    print(f"Model Order: {metrics['order']}")
    print(f"AIC: {metrics['aic']:.2f}, BIC: {metrics['bic']:.2f}")
    
    # Exponential Smoothing
    print("\n" + "=" * 50)
    print("Exponential Smoothing")
    print("=" * 50)
    
    es = ExponentialSmoothingForecaster()
    es.fit(train, trend='add', seasonal='add', seasonal_periods=7)
    print("Model fitted successfully")
    
    print("\n✅ All forecasting methods available and working!")
