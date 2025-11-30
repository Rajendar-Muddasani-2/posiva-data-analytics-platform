"""
Test Time Analytics Module
Performance optimization and test time analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TestTimeAnalytics:
    """
    Test time analysis and optimization
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with test results DataFrame
        
        Args:
            df: DataFrame with columns: device_id, test_name, test_time_ms, result
        """
        self.df = df
        self.logger = logger
        self.logger.info(f"Initialized TestTimeAnalytics with {len(df):,} records")
    
    def overall_statistics(self) -> Dict:
        """Calculate overall test time statistics"""
        stats = {
            'total_time_ms': float(self.df['test_time_ms'].sum()),
            'avg_time_ms': float(self.df['test_time_ms'].mean()),
            'median_time_ms': float(self.df['test_time_ms'].median()),
            'std_time_ms': float(self.df['test_time_ms'].std()),
            'min_time_ms': float(self.df['test_time_ms'].min()),
            'max_time_ms': float(self.df['test_time_ms'].max()),
            'avg_device_time_ms': float(self.df.groupby('device_id')['test_time_ms'].sum().mean()),
            'total_devices': int(self.df['device_id'].nunique())
        }
        
        # Calculate total test time in hours
        stats['total_time_hours'] = stats['total_time_ms'] / (1000 * 60 * 60)
        stats['avg_device_time_sec'] = stats['avg_device_time_ms'] / 1000
        
        return stats
    
    def time_by_test(self) -> pd.DataFrame:
        """Calculate test time statistics by test"""
        test_stats = self.df.groupby('test_name').agg({
            'test_time_ms': ['count', 'mean', 'median', 'std', 'min', 'max', 'sum']
        }).round(2)
        
        test_stats.columns = ['count', 'mean', 'median', 'std', 'min', 'max', 'total']
        test_stats = test_stats.sort_values('total', ascending=False)
        
        # Calculate percentage contribution
        test_stats['pct_total'] = (test_stats['total'] / test_stats['total'].sum() * 100).round(2)
        
        return test_stats.reset_index()
    
    def time_by_result(self) -> pd.DataFrame:
        """Compare test times between pass and fail"""
        result_stats = self.df.groupby('result')['test_time_ms'].agg([
            'count', 'mean', 'median', 'std', 'min', 'max'
        ]).round(2)
        
        return result_stats
    
    def slowest_tests(self, top_n: int = 10) -> pd.DataFrame:
        """Identify slowest tests"""
        test_times = self.df.groupby('test_name')['test_time_ms'].agg([
            'mean', 'max', 'count'
        ]).sort_values('mean', ascending=False).head(top_n)
        
        return test_times.reset_index()
    
    def test_time_outliers(self, threshold: float = 3.0) -> pd.DataFrame:
        """
        Detect test time outliers using Z-score
        
        Args:
            threshold: Z-score threshold (default 3.0)
            
        Returns:
            DataFrame with outlier records
        """
        z_scores = np.abs((self.df['test_time_ms'] - self.df['test_time_ms'].mean()) / 
                          self.df['test_time_ms'].std())
        
        outliers = self.df[z_scores > threshold].copy()
        outliers['z_score'] = z_scores[z_scores > threshold]
        
        return outliers.sort_values('z_score', ascending=False)
    
    def pareto_test_time(self, top_n: int = 10) -> pd.DataFrame:
        """Pareto analysis of test time contributors"""
        test_times = self.df.groupby('test_name')['test_time_ms'].sum().sort_values(ascending=False)
        
        pareto_df = pd.DataFrame({
            'test_name': test_times.head(top_n).index,
            'total_time': test_times.head(top_n).values,
            'percentage': (test_times.head(top_n).values / test_times.sum() * 100).round(2)
        })
        
        pareto_df['cumulative_pct'] = pareto_df['percentage'].cumsum()
        
        return pareto_df
    
    def optimization_opportunities(self) -> Dict:
        """Identify test time optimization opportunities"""
        test_stats = self.time_by_test()
        
        # Tests with high variability (std/mean > 0.5)
        high_variability = test_stats[
            (test_stats['std'] / test_stats['mean']) > 0.5
        ]['test_name'].tolist()
        
        # Tests contributing >10% of total time
        high_contributors = test_stats[test_stats['pct_total'] > 10]['test_name'].tolist()
        
        # Slowest tests (top 20%)
        cutoff = int(len(test_stats) * 0.2)
        slow_tests = test_stats.head(cutoff)['test_name'].tolist()
        
        return {
            'high_variability': high_variability,
            'high_contributors': high_contributors,
            'slow_tests': slow_tests,
            'potential_savings': self._calculate_potential_savings()
        }
    
    def _calculate_potential_savings(self) -> Dict:
        """Calculate potential time savings"""
        test_stats = self.time_by_test()
        
        # If top 3 tests reduced by 20%
        top_3_time = test_stats.head(3)['total'].sum()
        savings_20pct = top_3_time * 0.2
        
        # If all tests at 90th percentile
        current_time = self.df['test_time_ms'].sum()
        p90_time = self.df['test_time_ms'].quantile(0.90)
        all_at_p90 = len(self.df) * p90_time
        
        return {
            'top_3_reduction_20pct_ms': float(savings_20pct),
            'top_3_reduction_20pct_pct': float(savings_20pct / current_time * 100),
            'all_at_p90_savings_ms': float(max(0, current_time - all_at_p90)),
            'all_at_p90_savings_pct': float(max(0, (current_time - all_at_p90) / current_time * 100))
        }
    
    def plot_test_time_distribution(self) -> go.Figure:
        """Plot test time distribution"""
        fig = px.histogram(
            self.df,
            x='test_time_ms',
            nbins=50,
            title='Test Time Distribution',
            labels={'test_time_ms': 'Test Time (ms)'},
            marginal='box'
        )
        
        fig.update_layout(
            showlegend=False,
            template='plotly_white'
        )
        
        return fig
    
    def plot_time_by_test(self, top_n: int = 10) -> go.Figure:
        """Plot test time by test name"""
        test_stats = self.time_by_test().head(top_n)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=test_stats['test_name'],
            y=test_stats['mean'],
            name='Mean',
            marker_color='lightblue',
            text=test_stats['mean'].round(1),
            textposition='outside'
        ))
        
        fig.update_layout(
            title=f'Top {top_n} Tests by Average Time',
            xaxis_title='Test Name',
            yaxis_title='Average Time (ms)',
            xaxis_tickangle=45,
            template='plotly_white'
        )
        
        return fig
    
    def plot_pareto_chart(self, top_n: int = 10) -> go.Figure:
        """Plot Pareto chart for test time"""
        pareto_df = self.pareto_test_time(top_n)
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Bar chart
        fig.add_trace(
            go.Bar(
                x=pareto_df['test_name'],
                y=pareto_df['total_time'],
                name='Total Time (ms)',
                marker_color='steelblue'
            ),
            secondary_y=False
        )
        
        # Line chart (cumulative)
        fig.add_trace(
            go.Scatter(
                x=pareto_df['test_name'],
                y=pareto_df['cumulative_pct'],
                name='Cumulative %',
                line=dict(color='red', width=2),
                mode='lines+markers'
            ),
            secondary_y=True
        )
        
        fig.update_xaxes(title_text="Test Name", tickangle=45)
        fig.update_yaxes(title_text="Total Time (ms)", secondary_y=False)
        fig.update_yaxes(title_text="Cumulative %", range=[0, 105], secondary_y=True)
        
        fig.update_layout(
            title=f"Pareto Analysis: Top {top_n} Time Consumers",
            template='plotly_white',
            hovermode='x unified'
        )
        
        return fig
    
    def plot_time_by_result(self) -> go.Figure:
        """Plot test time comparison: pass vs fail"""
        fig = px.box(
            self.df,
            x='result',
            y='test_time_ms',
            title='Test Time by Result',
            color='result',
            color_discrete_map={'pass': 'green', 'fail': 'red'},
            labels={'test_time_ms': 'Test Time (ms)', 'result': 'Result'}
        )
        
        fig.update_layout(template='plotly_white')
        
        return fig
