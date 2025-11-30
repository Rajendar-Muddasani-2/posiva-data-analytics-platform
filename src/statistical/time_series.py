"""
Time Series Analysis Module
Forecasting and trend analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy import stats
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TimeSeriesAnalyzer:
    """
    Time series analysis and forecasting
    """
    
    def __init__(self, df: pd.DataFrame, date_col: Optional[str] = None):
        """
        Initialize time series analyzer
        
        Args:
            df: DataFrame with time series data
            date_col: Date column name (if None, uses index)
        """
        self.df = df.copy()
        self.date_col = date_col
        self.logger = logger
        
        # Ensure datetime index
        if date_col and date_col in df.columns:
            self.df[date_col] = pd.to_datetime(self.df[date_col])
            self.df = self.df.set_index(date_col)
        elif not isinstance(df.index, pd.DatetimeIndex):
            self.logger.warning("No datetime index found. Some functions may not work.")
    
    def aggregate_by_period(self, 
                           metric_col: str,
                           period: str = 'D',
                           agg_func: str = 'mean') -> pd.Series:
        """
        Aggregate data by time period
        
        Args:
            metric_col: Column to aggregate
            period: Pandas frequency ('D', 'W', 'M', etc.)
            agg_func: Aggregation function ('mean', 'sum', 'count', etc.)
            
        Returns:
            Aggregated time series
        """
        if not isinstance(self.df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame must have datetime index")
        
        ts = self.df[metric_col].resample(period).agg(agg_func)
        
        return ts
    
    def trend_analysis(self, metric_col: str, period: str = 'D') -> Dict:
        """
        Analyze trend in time series
        
        Args:
            metric_col: Column to analyze
            period: Aggregation period
            
        Returns:
            Dictionary with trend statistics
        """
        ts = self.aggregate_by_period(metric_col, period)
        
        # Remove NaN
        ts = ts.dropna()
        
        if len(ts) < 2:
            return {'error': 'Insufficient data'}
        
        # Linear regression for trend
        x = np.arange(len(ts))
        y = ts.values
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        # Calculate trend direction
        if p_value < 0.05:
            if slope > 0:
                trend = 'increasing'
            else:
                trend = 'decreasing'
        else:
            trend = 'stable'
        
        return {
            'slope': float(slope),
            'intercept': float(intercept),
            'r_squared': float(r_value ** 2),
            'p_value': float(p_value),
            'trend': trend,
            'start_value': float(ts.iloc[0]),
            'end_value': float(ts.iloc[-1]),
            'change': float(ts.iloc[-1] - ts.iloc[0]),
            'change_pct': float((ts.iloc[-1] - ts.iloc[0]) / ts.iloc[0] * 100) if ts.iloc[0] != 0 else 0
        }
    
    def moving_average(self, 
                      metric_col: str,
                      window: int = 7,
                      center: bool = True) -> pd.Series:
        """
        Calculate moving average
        
        Args:
            metric_col: Column to smooth
            window: Window size
            center: Center the window
            
        Returns:
            Moving average series
        """
        ma = self.df[metric_col].rolling(window=window, center=center).mean()
        
        return ma
    
    def exponential_smoothing(self,
                             metric_col: str,
                             alpha: float = 0.3) -> pd.Series:
        """
        Exponential weighted moving average
        
        Args:
            metric_col: Column to smooth
            alpha: Smoothing parameter (0-1)
            
        Returns:
            Smoothed series
        """
        ema = self.df[metric_col].ewm(alpha=alpha, adjust=False).mean()
        
        return ema
    
    def seasonality_detection(self, 
                             metric_col: str,
                             period: int = 7) -> Dict:
        """
        Detect seasonality using autocorrelation
        
        Args:
            metric_col: Column to analyze
            period: Expected period (e.g., 7 for weekly)
            
        Returns:
            Dictionary with seasonality stats
        """
        ts = self.df[metric_col].dropna()
        
        if len(ts) < period * 2:
            return {'error': 'Insufficient data for seasonality detection'}
        
        # Calculate autocorrelation at lag=period
        from statsmodels.tsa.stattools import acf
        
        acf_values = acf(ts, nlags=period)
        acf_at_period = acf_values[period]
        
        # Simple threshold-based detection
        has_seasonality = abs(acf_at_period) > 0.3
        
        return {
            'period': period,
            'autocorrelation': float(acf_at_period),
            'has_seasonality': bool(has_seasonality),
            'strength': 'strong' if abs(acf_at_period) > 0.6 else 'moderate' if abs(acf_at_period) > 0.3 else 'weak'
        }
    
    def forecast_simple(self,
                       metric_col: str,
                       periods: int = 7,
                       method: str = 'moving_average') -> pd.Series:
        """
        Simple forecasting methods
        
        Args:
            metric_col: Column to forecast
            periods: Number of periods to forecast
            method: 'moving_average', 'exponential', or 'last_value'
            
        Returns:
            Forecast series
        """
        ts = self.df[metric_col].dropna()
        
        if method == 'moving_average':
            # Use last 7 values
            forecast_value = ts.tail(7).mean()
        elif method == 'exponential':
            # Use exponential smoothing
            forecast_value = self.exponential_smoothing(metric_col).iloc[-1]
        elif method == 'last_value':
            # Naive forecast (use last value)
            forecast_value = ts.iloc[-1]
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Create forecast index
        last_date = ts.index[-1] if isinstance(ts.index, pd.DatetimeIndex) else None
        
        if last_date:
            forecast_index = pd.date_range(start=last_date, periods=periods+1, freq='D')[1:]
        else:
            forecast_index = range(len(ts), len(ts) + periods)
        
        # Simple forecast (constant value)
        forecast = pd.Series([forecast_value] * periods, index=forecast_index)
        
        return forecast
    
    def plot_trend(self, 
                  metric_col: str,
                  period: str = 'D',
                  show_ma: bool = True,
                  ma_window: int = 7) -> go.Figure:
        """
        Plot time series with trend
        
        Args:
            metric_col: Column to plot
            period: Aggregation period
            show_ma: Show moving average
            ma_window: MA window size
            
        Returns:
            Plotly figure
        """
        ts = self.aggregate_by_period(metric_col, period)
        
        fig = go.Figure()
        
        # Original data
        fig.add_trace(go.Scatter(
            x=ts.index,
            y=ts.values,
            mode='lines+markers',
            name='Actual',
            line=dict(color='blue', width=1),
            marker=dict(size=4)
        ))
        
        # Moving average
        if show_ma:
            ma = ts.rolling(window=ma_window, center=True).mean()
            fig.add_trace(go.Scatter(
                x=ma.index,
                y=ma.values,
                mode='lines',
                name=f'{ma_window}-period MA',
                line=dict(color='red', width=2)
            ))
        
        # Trend line
        trend = self.trend_analysis(metric_col, period)
        if 'slope' in trend:
            x_vals = np.arange(len(ts))
            trend_line = trend['slope'] * x_vals + trend['intercept']
            
            fig.add_trace(go.Scatter(
                x=ts.index,
                y=trend_line,
                mode='lines',
                name='Trend',
                line=dict(color='green', width=2, dash='dash')
            ))
        
        fig.update_layout(
            title=f'Time Series: {metric_col}',
            xaxis_title='Date',
            yaxis_title=metric_col,
            hovermode='x unified',
            template='plotly_white'
        )
        
        return fig
    
    def plot_forecast(self,
                     metric_col: str,
                     periods: int = 7,
                     method: str = 'moving_average') -> go.Figure:
        """
        Plot historical data with forecast
        
        Args:
            metric_col: Column to forecast
            periods: Forecast periods
            method: Forecast method
            
        Returns:
            Plotly figure
        """
        ts = self.df[metric_col].dropna()
        forecast = self.forecast_simple(metric_col, periods, method)
        
        fig = go.Figure()
        
        # Historical
        fig.add_trace(go.Scatter(
            x=ts.index,
            y=ts.values,
            mode='lines+markers',
            name='Historical',
            line=dict(color='blue')
        ))
        
        # Forecast
        fig.add_trace(go.Scatter(
            x=forecast.index,
            y=forecast.values,
            mode='lines+markers',
            name='Forecast',
            line=dict(color='red', dash='dash')
        ))
        
        fig.update_layout(
            title=f'Forecast: {metric_col} ({method})',
            xaxis_title='Date',
            yaxis_title=metric_col,
            hovermode='x unified',
            template='plotly_white'
        )
        
        return fig


class ABTestAnalyzer:
    """
    A/B Testing framework
    """
    
    def __init__(self):
        self.logger = logger
    
    def analyze_ab_test(self,
                       group_a: pd.Series,
                       group_b: pd.Series,
                       metric_name: str = 'metric') -> Dict:
        """
        Perform A/B test analysis
        
        Args:
            group_a: Control group data
            group_b: Treatment group data
            metric_name: Name of metric
            
        Returns:
            Dictionary with test results
        """
        # Remove NaN
        group_a = group_a.dropna()
        group_b = group_b.dropna()
        
        if len(group_a) < 2 or len(group_b) < 2:
            return {'error': 'Insufficient data'}
        
        # Statistics
        mean_a = group_a.mean()
        mean_b = group_b.mean()
        std_a = group_a.std()
        std_b = group_b.std()
        
        # T-test
        t_stat, p_value = stats.ttest_ind(group_a, group_b)
        
        # Effect size (Cohen's d)
        pooled_std = np.sqrt((std_a**2 + std_b**2) / 2)
        cohens_d = (mean_b - mean_a) / pooled_std if pooled_std > 0 else 0
        
        # Confidence interval for difference
        diff = mean_b - mean_a
        se_diff = np.sqrt(std_a**2/len(group_a) + std_b**2/len(group_b))
        ci_lower = diff - 1.96 * se_diff
        ci_upper = diff + 1.96 * se_diff
        
        # Relative improvement
        improvement_pct = (mean_b - mean_a) / mean_a * 100 if mean_a != 0 else 0
        
        return {
            'metric': metric_name,
            'n_a': len(group_a),
            'n_b': len(group_b),
            'mean_a': float(mean_a),
            'mean_b': float(mean_b),
            'std_a': float(std_a),
            'std_b': float(std_b),
            'difference': float(diff),
            'improvement_pct': float(improvement_pct),
            't_statistic': float(t_stat),
            'p_value': float(p_value),
            'significant': bool(p_value < 0.05),
            'cohens_d': float(cohens_d),
            'effect_size': 'large' if abs(cohens_d) >= 0.8 else 'medium' if abs(cohens_d) >= 0.5 else 'small',
            'ci_lower': float(ci_lower),
            'ci_upper': float(ci_upper),
            'recommendation': 'Deploy B' if p_value < 0.05 and mean_b > mean_a else 'Keep A' if p_value < 0.05 else 'Inconclusive'
        }
    
    def sample_size_calculator(self,
                              baseline_mean: float,
                              baseline_std: float,
                              min_detectable_effect: float = 0.05,
                              alpha: float = 0.05,
                              power: float = 0.8) -> int:
        """
        Calculate required sample size for A/B test
        
        Args:
            baseline_mean: Control group mean
            baseline_std: Control group std
            min_detectable_effect: Minimum effect to detect (as proportion)
            alpha: Type I error rate
            power: Statistical power (1 - Type II error)
            
        Returns:
            Required sample size per group
        """
        from scipy.stats import norm
        
        # Calculate effect size
        delta = baseline_mean * min_detectable_effect
        cohens_d = delta / baseline_std
        
        # Z-scores
        z_alpha = norm.ppf(1 - alpha/2)
        z_beta = norm.ppf(power)
        
        # Sample size formula
        n = 2 * ((z_alpha + z_beta) / cohens_d) ** 2
        
        return int(np.ceil(n))
