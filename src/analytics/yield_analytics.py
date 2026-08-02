"""
Yield Analytics Module
Comprehensive yield analysis and metrics
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from src.utils.logger import get_logger

logger = get_logger(__name__)


class YieldAnalytics:
    """
    Yield analysis and visualization
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with test results DataFrame
        
        Args:
            df: DataFrame with columns: device_id, test_name, result, lot_id, wafer_id
        """
        self.df = df
        self.logger = logger
        self.logger.info(f"Initialized YieldAnalytics with {len(df):,} records")
    
    def calculate_overall_yield(self) -> float:
        """
        Calculate overall yield (device level)
        
        Returns:
            Yield percentage
        """
        device_results = self.df.groupby('device_id')['result'].apply(
            lambda x: 'pass' if (x == 'pass').all() else 'fail'
        )
        yield_rate = (device_results == 'pass').sum() / len(device_results) * 100
        
        self.logger.info(f"Overall yield: {yield_rate:.2f}%")
        return yield_rate
    
    def yield_by_lot(self) -> pd.DataFrame:
        """Calculate yield by lot"""
        lot_yield = self.df.groupby(['lot_id', 'device_id'])['result'].apply(
            lambda x: 1 if (x == 'pass').all() else 0
        ).groupby('lot_id').agg(['sum', 'count', 'mean'])
        
        lot_yield.columns = ['passing_devices', 'total_devices', 'yield']
        lot_yield['yield'] = lot_yield['yield'] * 100
        
        return lot_yield.reset_index()
    
    def yield_by_wafer(self) -> pd.DataFrame:
        """Calculate yield by wafer"""
        if 'wafer_id' not in self.df.columns:
            self.logger.warning("wafer_id column not found")
            return pd.DataFrame()
        
        wafer_yield = self.df.groupby(['wafer_id', 'device_id'])['result'].apply(
            lambda x: 1 if (x == 'pass').all() else 0
        ).groupby('wafer_id').agg(['sum', 'count', 'mean'])
        
        wafer_yield.columns = ['passing_devices', 'total_devices', 'yield']
        wafer_yield['yield'] = wafer_yield['yield'] * 100
        
        return wafer_yield.reset_index()
    
    def yield_by_test(self) -> pd.DataFrame:
        """Calculate yield by individual test"""
        test_yield = self.df.groupby('test_name')['result'].apply(
            lambda x: (x == 'pass').sum() / len(x) * 100
        ).sort_values(ascending=False)
        
        return test_yield.reset_index(name='yield')
    
    def failing_tests_pareto(self, top_n: int = 10) -> pd.DataFrame:
        """
        Pareto analysis of failing tests
        
        Args:
            top_n: Number of top failing tests to return
            
        Returns:
            DataFrame with test failures and cumulative percentage
        """
        fail_counts = self.df[self.df['result'] == 'fail'].groupby('test_name').size()
        fail_counts = fail_counts.sort_values(ascending=False).head(top_n)
        
        pareto_df = pd.DataFrame({
            'test_name': fail_counts.index,
            'failures': fail_counts.values,
            'percentage': (fail_counts.values / fail_counts.sum() * 100).round(2)
        })
        
        pareto_df['cumulative_pct'] = pareto_df['percentage'].cumsum()
        
        return pareto_df
    
    def plot_yield_trend(self, by: str = 'lot') -> go.Figure:
        """
        Plot yield trend
        
        Args:
            by: Group by 'lot' or 'wafer'
            
        Returns:
            Plotly figure
        """
        if by == 'lot':
            yield_df = self.yield_by_lot()
            x_col, title = 'lot_id', 'Yield Trend by Lot'
        elif by == 'wafer':
            yield_df = self.yield_by_wafer()
            x_col, title = 'wafer_id', 'Yield Trend by Wafer'
        else:
            raise ValueError("by must be 'lot' or 'wafer'")
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=yield_df[x_col],
            y=yield_df['yield'],
            name='Yield %',
            marker_color='lightblue',
            text=yield_df['yield'].round(1),
            textposition='outside'
        ))
        
        # Add target line (assuming 90% target)
        fig.add_hline(y=90, line_dash="dash", line_color="red", 
                     annotation_text="Target: 90%")
        
        fig.update_layout(
            title=title,
            xaxis_title=x_col.replace('_', ' ').title(),
            yaxis_title='Yield (%)',
            yaxis_range=[0, 105],
            showlegend=False,
            template='plotly_white'
        )
        
        return fig
    
    def plot_pareto(self, top_n: int = 10) -> go.Figure:
        """
        Plot Pareto chart of failing tests
        
        Args:
            top_n: Number of top failing tests
            
        Returns:
            Plotly figure
        """
        pareto_df = self.failing_tests_pareto(top_n)
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Bar chart
        fig.add_trace(
            go.Bar(
                x=pareto_df['test_name'],
                y=pareto_df['failures'],
                name='Failures',
                marker_color='lightcoral'
            ),
            secondary_y=False
        )
        
        # Line chart (cumulative)
        fig.add_trace(
            go.Scatter(
                x=pareto_df['test_name'],
                y=pareto_df['cumulative_pct'],
                name='Cumulative %',
                line=dict(color='blue', width=2),
                mode='lines+markers'
            ),
            secondary_y=True
        )
        
        fig.update_xaxes(title_text="Test Name")
        fig.update_yaxes(title_text="Failure Count", secondary_y=False)
        fig.update_yaxes(title_text="Cumulative %", range=[0, 105], secondary_y=True)
        
        fig.update_layout(
            title=f"Pareto Analysis: Top {top_n} Failing Tests",
            template='plotly_white',
            hovermode='x unified'
        )
        
        return fig
    
    def plot_yield_distribution(self) -> go.Figure:
        """Plot yield distribution across devices"""
        device_pass_rate = self.df.groupby('device_id')['result'].apply(
            lambda x: (x == 'pass').sum() / len(x) * 100
        )
        
        fig = px.histogram(
            device_pass_rate,
            nbins=20,
            title='Device Yield Distribution',
            labels={'value': 'Yield (%)', 'count': 'Number of Devices'},
            color_discrete_sequence=['lightgreen']
        )
        
        fig.update_layout(
            xaxis_title='Yield (%)',
            yaxis_title='Number of Devices',
            showlegend=False,
            template='plotly_white'
        )
        
        return fig
    
    def generate_summary(self) -> Dict:
        """Generate yield summary statistics"""
        overall_yield = self.calculate_overall_yield()
        lot_yield = self.yield_by_lot()
        test_yield = self.yield_by_test()
        
        summary = {
            'overall_yield': overall_yield,
            'total_devices': self.df['device_id'].nunique(),
            'passing_devices': int((self.df.groupby('device_id')['result'].apply(
                lambda x: (x == 'pass').all()
            )).sum()),
            'total_tests': len(self.df),
            'passing_tests': int((self.df['result'] == 'pass').sum()),
            'test_yield': float((self.df['result'] == 'pass').sum() / len(self.df) * 100),
            'lots': self.df['lot_id'].nunique() if 'lot_id' in self.df.columns else None,
            'lowest_yield_test': test_yield.iloc[-1]['test_name'] if len(test_yield) > 0 else None,
            'lowest_yield_value': float(test_yield.iloc[-1]['yield']) if len(test_yield) > 0 else None,
        }
        
        return summary


class YieldAnalyzer:
    """Adapter exposing test-compatible interface over YieldAnalytics.

    Normalizes column names so both Title_Case and snake_case datasets work.
    """
    _COL_MAP = {
        "device_id": ["device_id", "Device_ID", "DEVICE_ID"],
        "result":    ["result", "test_result", "Test_Result", "TEST_RESULT"],
        "wafer_id":  ["wafer_id", "Wafer_ID", "WAFER_ID"],
        "lot_id":    ["lot_id", "Lot_ID", "LOT_ID"],
    }

    def __init__(self, df):
        self._df = df.copy()
        self._normalize()

    def _normalize(self):
        mapping = {}
        for canonical, variants in self._COL_MAP.items():
            for v in variants:
                if v in self._df.columns and canonical not in self._df.columns:
                    mapping[v] = canonical
                    break
        if mapping:
            self._df = self._df.rename(columns=mapping)
        if "result" in self._df.columns:
            self._df["result"] = self._df["result"].astype(str).str.lower()

    def overall_yield(self):
        if "device_id" in self._df.columns:
            grouped = self._df.groupby("device_id")["result"].apply(
                lambda x: "pass" if (x == "pass").all() else "fail"
            )
            rate = (grouped == "pass").sum() / len(grouped) * 100
        else:
            rate = (self._df["result"] == "pass").sum() / len(self._df) * 100
        return {"Yield %": round(float(rate), 4)}

    def yield_by_wafer(self):
        col = "wafer_id" if "wafer_id" in self._df.columns else self._df.columns[0]
        result = self._df.groupby(col)["result"].apply(
            lambda x: (x == "pass").sum() / len(x) * 100
        ).reset_index()
        result.columns = [col, "Yield %"]
        # Normalise to canonical display name expected by tests
        result = result.rename(columns={col: "Wafer_ID"})
        return result

    def yield_by_lot(self):
        if "lot_id" not in self._df.columns:
            return self._df.assign(lot_yield=lambda d: 100.0)
        return self._df.groupby("lot_id")["result"].apply(
            lambda x: (x == "pass").sum() / len(x) * 100
        ).reset_index().rename(columns={"lot_id": "Lot_ID", "result": "Yield %"})
