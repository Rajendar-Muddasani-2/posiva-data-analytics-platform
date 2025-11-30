"""
Parametric Analytics Module
Statistical analysis of parametric test measurements
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


class ParametricAnalytics:
    """
    Parametric test analysis and capability studies
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with test results DataFrame
        
        Args:
            df: DataFrame with columns: device_id, test_name, measured_value, 
                lower_limit, upper_limit, result
        """
        self.df = df
        # Filter to parametric tests (those with measured values)
        self.parametric_df = df[df['measured_value'].notna()].copy()
        self.logger = logger
        self.logger.info(f"Initialized ParametricAnalytics with {len(self.parametric_df):,} parametric records")
    
    def cpk_analysis(self, test_name: Optional[str] = None) -> pd.DataFrame:
        """
        Calculate Cpk (Process Capability Index) for tests
        
        Args:
            test_name: Specific test name (optional, default all tests)
            
        Returns:
            DataFrame with Cpk metrics
        """
        if test_name:
            df = self.parametric_df[self.parametric_df['test_name'] == test_name]
        else:
            df = self.parametric_df
        
        results = []
        
        for test in df['test_name'].unique():
            test_data = df[df['test_name'] == test]
            
            if len(test_data) < 2:
                continue
            
            values = test_data['measured_value']
            lsl = test_data['lower_limit'].iloc[0]
            usl = test_data['upper_limit'].iloc[0]
            
            mean = values.mean()
            std = values.std()
            
            if std == 0:
                continue
            
            # Calculate Cp and Cpk
            cp = (usl - lsl) / (6 * std) if pd.notna(lsl) and pd.notna(usl) else None
            
            cpu = (usl - mean) / (3 * std) if pd.notna(usl) else None
            cpl = (mean - lsl) / (3 * std) if pd.notna(lsl) else None
            
            if cpu is not None and cpl is not None:
                cpk = min(cpu, cpl)
            elif cpu is not None:
                cpk = cpu
            elif cpl is not None:
                cpk = cpl
            else:
                cpk = None
            
            results.append({
                'test_name': test,
                'count': len(test_data),
                'mean': mean,
                'std': std,
                'lsl': lsl,
                'usl': usl,
                'cp': cp,
                'cpk': cpk,
                'cpu': cpu,
                'cpl': cpl
            })
        
        cpk_df = pd.DataFrame(results)
        cpk_df = cpk_df.sort_values('cpk', ascending=True) if 'cpk' in cpk_df else cpk_df
        
        return cpk_df
    
    def distribution_fit(self, test_name: str) -> Dict:
        """
        Fit normal distribution and perform goodness-of-fit test
        
        Args:
            test_name: Test name to analyze
            
        Returns:
            Dictionary with fit statistics
        """
        test_data = self.parametric_df[self.parametric_df['test_name'] == test_name]['measured_value']
        
        if len(test_data) < 3:
            return {'error': 'Insufficient data'}
        
        # Fit normal distribution
        mu, sigma = stats.norm.fit(test_data)
        
        # Shapiro-Wilk test for normality
        if len(test_data) >= 3 and len(test_data) <= 5000:
            shapiro_stat, shapiro_p = stats.shapiro(test_data)
        else:
            shapiro_stat, shapiro_p = None, None
        
        # Kolmogorov-Smirnov test
        ks_stat, ks_p = stats.kstest(test_data, 'norm', args=(mu, sigma))
        
        return {
            'test_name': test_name,
            'count': len(test_data),
            'mean': float(mu),
            'std': float(sigma),
            'shapiro_stat': float(shapiro_stat) if shapiro_stat else None,
            'shapiro_pvalue': float(shapiro_p) if shapiro_p else None,
            'ks_stat': float(ks_stat),
            'ks_pvalue': float(ks_p),
            'is_normal': bool(ks_p > 0.05) if ks_p else None
        }
    
    def outlier_detection(self, test_name: str, method: str = 'zscore', threshold: float = 3.0) -> pd.DataFrame:
        """
        Detect outliers in parametric data
        
        Args:
            test_name: Test name to analyze
            method: 'zscore' or 'iqr'
            threshold: Z-score threshold (default 3.0) or IQR multiplier (default 1.5)
            
        Returns:
            DataFrame with outliers
        """
        test_data = self.parametric_df[self.parametric_df['test_name'] == test_name].copy()
        
        values = test_data['measured_value']
        
        if method == 'zscore':
            z_scores = np.abs((values - values.mean()) / values.std())
            test_data['outlier_score'] = z_scores
            outliers = test_data[z_scores > threshold]
        
        elif method == 'iqr':
            Q1 = values.quantile(0.25)
            Q3 = values.quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - threshold * IQR
            upper = Q3 + threshold * IQR
            test_data['outlier_score'] = np.maximum(lower - values, values - upper)
            outliers = test_data[(values < lower) | (values > upper)]
        
        else:
            raise ValueError("method must be 'zscore' or 'iqr'")
        
        return outliers.sort_values('outlier_score', ascending=False)
    
    def correlation_analysis(self) -> pd.DataFrame:
        """Analyze correlations between parametric tests"""
        # Pivot to wide format
        pivot_df = self.parametric_df.pivot_table(
            index='device_id',
            columns='test_name',
            values='measured_value'
        )
        
        # Calculate correlation matrix
        corr_matrix = pivot_df.corr()
        
        # Extract high correlations
        high_corr = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) > 0.7 and pd.notna(corr_val):
                    high_corr.append({
                        'test1': corr_matrix.columns[i],
                        'test2': corr_matrix.columns[j],
                        'correlation': float(corr_val)
                    })
        
        high_corr_df = pd.DataFrame(high_corr).sort_values('correlation', key=abs, ascending=False)
        
        return high_corr_df
    
    def margin_analysis(self) -> pd.DataFrame:
        """
        Analyze test margins (distance to limits)
        
        Returns:
            DataFrame with margin statistics
        """
        margin_stats = []
        
        for test in self.parametric_df['test_name'].unique():
            test_data = self.parametric_df[self.parametric_df['test_name'] == test]
            
            values = test_data['measured_value']
            lsl = test_data['lower_limit'].iloc[0]
            usl = test_data['upper_limit'].iloc[0]
            
            # Calculate margins
            if pd.notna(lsl) and pd.notna(usl):
                lower_margin = (values - lsl).min()
                upper_margin = (usl - values).min()
                min_margin = min(lower_margin, upper_margin)
            elif pd.notna(lsl):
                min_margin = (values - lsl).min()
                lower_margin = min_margin
                upper_margin = None
            elif pd.notna(usl):
                min_margin = (usl - values).min()
                lower_margin = None
                upper_margin = min_margin
            else:
                continue
            
            margin_stats.append({
                'test_name': test,
                'min_margin': float(min_margin),
                'lower_margin': float(lower_margin) if lower_margin is not None else None,
                'upper_margin': float(upper_margin) if upper_margin is not None else None,
                'at_risk': bool(min_margin < 0)
            })
        
        return pd.DataFrame(margin_stats).sort_values('min_margin')
    
    def plot_distribution(self, test_name: str) -> go.Figure:
        """Plot distribution with limits"""
        test_data = self.parametric_df[self.parametric_df['test_name'] == test_name]
        
        values = test_data['measured_value']
        lsl = test_data['lower_limit'].iloc[0]
        usl = test_data['upper_limit'].iloc[0]
        
        fig = go.Figure()
        
        # Histogram
        fig.add_trace(go.Histogram(
            x=values,
            name='Measurements',
            nbinsx=30,
            marker_color='lightblue'
        ))
        
        # Add limits
        if pd.notna(lsl):
            fig.add_vline(x=lsl, line_dash="dash", line_color="red", annotation_text="LSL")
        if pd.notna(usl):
            fig.add_vline(x=usl, line_dash="dash", line_color="red", annotation_text="USL")
        
        # Add mean
        fig.add_vline(x=values.mean(), line_dash="dot", line_color="green", annotation_text="Mean")
        
        fig.update_layout(
            title=f'Distribution: {test_name}',
            xaxis_title='Measured Value',
            yaxis_title='Count',
            template='plotly_white'
        )
        
        return fig
    
    def plot_cpk_chart(self, top_n: int = 10) -> go.Figure:
        """Plot Cpk values"""
        cpk_df = self.cpk_analysis().head(top_n)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=cpk_df['test_name'],
            y=cpk_df['cpk'],
            marker_color=cpk_df['cpk'].apply(lambda x: 'green' if x >= 1.33 else 'orange' if x >= 1.0 else 'red'),
            text=cpk_df['cpk'].round(2),
            textposition='outside'
        ))
        
        # Add reference lines
        fig.add_hline(y=1.33, line_dash="dash", line_color="green", annotation_text="Cpk = 1.33 (Capable)")
        fig.add_hline(y=1.0, line_dash="dash", line_color="orange", annotation_text="Cpk = 1.0 (Marginal)")
        
        fig.update_layout(
            title=f'Process Capability (Cpk) - Bottom {top_n} Tests',
            xaxis_title='Test Name',
            yaxis_title='Cpk',
            xaxis_tickangle=45,
            template='plotly_white',
            showlegend=False
        )
        
        return fig
    
    def plot_correlation_heatmap(self) -> go.Figure:
        """Plot correlation heatmap"""
        pivot_df = self.parametric_df.pivot_table(
            index='device_id',
            columns='test_name',
            values='measured_value'
        )
        
        corr_matrix = pivot_df.corr()
        
        fig = px.imshow(
            corr_matrix,
            title='Parametric Test Correlations',
            color_continuous_scale='RdBu_r',
            zmin=-1, zmax=1,
            text_auto='.2f'
        )
        
        return fig
