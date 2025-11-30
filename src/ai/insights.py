"""
AI-Powered Insights Module

This module provides AI capabilities for:
- Natural Language Generation (NLG) for automated insights
- Automated Root Cause Analysis (RCA)
- Model explainability with SHAP and LIME
- Intelligent recommendations

Author: POSIVA Analytics Team
Date: 2024
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

# Explainability
import shap
from lime import lime_tabular

# Visualization
import plotly.graph_objects as go
import plotly.express as px

logger = logging.getLogger(__name__)


class InsightGenerator:
    """
    Natural Language Generation for Automated Insights
    
    Generates human-readable insights from data analysis results.
    """
    
    def __init__(self):
        """Initialize insight generator"""
        self.templates = self._load_templates()
        
    def _load_templates(self) -> Dict:
        """Load insight templates"""
        return {
            'yield': {
                'excellent': "✅ Excellent yield performance at {value:.2f}%, exceeding target of {target:.2f}% by {diff:.2f} percentage points.",
                'good': "👍 Good yield at {value:.2f}%, meeting target of {target:.2f}%.",
                'warning': "⚠️ Yield at {value:.2f}% is below target of {target:.2f}% by {diff:.2f} percentage points.",
                'critical': "🚨 Critical: Yield dropped to {value:.2f}%, significantly below target of {target:.2f}% (deficit: {diff:.2f}pp)."
            },
            'trend': {
                'improving': "📈 Positive trend detected: {metric} improving by {rate:.2f}% over the last {period} days.",
                'declining': "📉 Negative trend detected: {metric} declining by {rate:.2f}% over the last {period} days.",
                'stable': "➡️ {metric} remains stable with minimal variation (±{variation:.2f}%)."
            },
            'anomaly': {
                'detected': "🔍 Anomaly detected in {context}: {details}. Immediate investigation recommended.",
                'none': "✅ No anomalies detected. All metrics within normal ranges."
            },
            'comparison': {
                'better': "✅ {metric} improved by {improvement:.2f}% compared to {baseline}.",
                'worse': "⚠️ {metric} degraded by {decline:.2f}% compared to {baseline}.",
                'similar': "➡️ {metric} similar to {baseline} (difference: {diff:.2f}%)."
            }
        }
    
    def generate_yield_insight(self, current_yield: float, target_yield: float = 95.0) -> str:
        """
        Generate insight about yield performance
        
        Args:
            current_yield: Current yield percentage
            target_yield: Target yield percentage
            
        Returns:
            Human-readable insight string
        """
        diff = abs(current_yield - target_yield)
        
        if current_yield >= target_yield + 2:
            template = self.templates['yield']['excellent']
        elif current_yield >= target_yield:
            template = self.templates['yield']['good']
        elif current_yield >= target_yield - 2:
            template = self.templates['yield']['warning']
        else:
            template = self.templates['yield']['critical']
        
        return template.format(value=current_yield, target=target_yield, diff=diff)
    
    def generate_trend_insight(self, metric_name: str, values: List[float], 
                              period_days: int = 7) -> str:
        """
        Generate insight about trend
        
        Args:
            metric_name: Name of the metric
            values: Time series values
            period_days: Number of days in analysis period
            
        Returns:
            Human-readable trend insight
        """
        if len(values) < 2:
            return f"Insufficient data for {metric_name} trend analysis."
        
        # Calculate trend
        start_val = values[0]
        end_val = values[-1]
        change_pct = ((end_val - start_val) / start_val) * 100
        variation = np.std(values) / np.mean(values) * 100
        
        if abs(change_pct) < 1:  # Less than 1% change
            template = self.templates['trend']['stable']
            return template.format(metric=metric_name, variation=variation)
        elif change_pct > 0:
            template = self.templates['trend']['improving']
            return template.format(metric=metric_name, rate=change_pct, period=period_days)
        else:
            template = self.templates['trend']['declining']
            return template.format(metric=metric_name, rate=abs(change_pct), period=period_days)
    
    def generate_summary_report(self, metrics: Dict) -> str:
        """
        Generate comprehensive summary report
        
        Args:
            metrics: Dictionary with analysis metrics
            
        Returns:
            Multi-paragraph summary report
        """
        report_parts = []
        
        # Header
        report_parts.append(f"📊 **Analysis Summary Report**")
        report_parts.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_parts.append("")
        
        # Overall performance
        if 'overall_yield' in metrics:
            report_parts.append("### Overall Performance")
            report_parts.append(self.generate_yield_insight(
                metrics['overall_yield'],
                metrics.get('target_yield', 95.0)
            ))
            report_parts.append("")
        
        # Key findings
        if 'key_findings' in metrics:
            report_parts.append("### Key Findings")
            for i, finding in enumerate(metrics['key_findings'], 1):
                report_parts.append(f"{i}. {finding}")
            report_parts.append("")
        
        # Recommendations
        if 'recommendations' in metrics:
            report_parts.append("### Recommendations")
            for i, rec in enumerate(metrics['recommendations'], 1):
                report_parts.append(f"{i}. {rec}")
            report_parts.append("")
        
        return "\n".join(report_parts)


class RootCauseAnalyzer:
    """
    Automated Root Cause Analysis
    
    Identifies potential root causes of failures using:
    - Statistical analysis
    - Pattern recognition
    - Correlation analysis
    """
    
    def __init__(self):
        """Initialize RCA engine"""
        self.analysis_results = None
        
    def analyze_failures(self, df: pd.DataFrame) -> Dict:
        """
        Analyze failure patterns
        
        Args:
            df: Test data with results
            
        Returns:
            Dictionary with root cause analysis
        """
        failures = df[df['result'] == 'FAIL'].copy()
        
        if len(failures) == 0:
            return {
                'failure_count': 0,
                'message': 'No failures detected - excellent performance!',
                'root_causes': []
            }
        
        analysis = {
            'failure_count': len(failures),
            'failure_rate': len(failures) / len(df) * 100,
            'root_causes': []
        }
        
        # 1. Test-based analysis
        test_failures = failures.groupby('test_name').size().sort_values(ascending=False)
        
        if len(test_failures) > 0:
            top_test = test_failures.index[0]
            top_test_count = test_failures.iloc[0]
            top_test_pct = (top_test_count / len(failures)) * 100
            
            if top_test_pct > 30:  # More than 30% of failures from one test
                analysis['root_causes'].append({
                    'category': 'Test Concentration',
                    'severity': 'HIGH' if top_test_pct > 50 else 'MEDIUM',
                    'description': f"{top_test} accounts for {top_test_pct:.1f}% of all failures ({top_test_count} failures)",
                    'recommendation': f"Focus investigation on {top_test}. Check test parameters, limits, and equipment calibration.",
                    'confidence': 0.9
                })
        
        # 2. Lot-based analysis
        lot_failures = failures.groupby('lot_id').size()
        lot_failure_rates = failures.groupby('lot_id').size() / df.groupby('lot_id').size() * 100
        
        problematic_lots = lot_failure_rates[lot_failure_rates > 10].sort_values(ascending=False)
        
        if len(problematic_lots) > 0:
            top_lot = problematic_lots.index[0]
            top_lot_rate = problematic_lots.iloc[0]
            
            analysis['root_causes'].append({
                'category': 'Lot Quality Issue',
                'severity': 'HIGH' if top_lot_rate > 20 else 'MEDIUM',
                'description': f"Lot {top_lot} has {top_lot_rate:.1f}% failure rate (significantly above average)",
                'recommendation': f"Review manufacturing process for Lot {top_lot}. Check for equipment issues or process deviations.",
                'confidence': 0.85
            })
        
        # 3. Parametric analysis (out-of-spec values)
        parametric_tests = failures[failures['test_type'] == 'parametric']
        
        if len(parametric_tests) > 0:
            # Check for out-of-spec patterns
            oos_count = parametric_tests['measured_value'].notna().sum()
            
            if oos_count > 0:
                analysis['root_causes'].append({
                    'category': 'Parametric Out-of-Spec',
                    'severity': 'MEDIUM',
                    'description': f"{oos_count} parametric test failures with out-of-spec measurements",
                    'recommendation': "Analyze parametric distributions. Consider limits review or process adjustment.",
                    'confidence': 0.75
                })
        
        # 4. Wafer-level clustering
        if 'wafer_id' in failures.columns:
            wafer_failures = failures.groupby('wafer_id').size()
            
            if len(wafer_failures) > 0 and wafer_failures.max() > len(failures) * 0.2:
                top_wafer = wafer_failures.idxmax()
                top_wafer_count = wafer_failures.max()
                
                analysis['root_causes'].append({
                    'category': 'Wafer-Level Issue',
                    'severity': 'HIGH',
                    'description': f"Wafer {top_wafer} has {top_wafer_count} failures (spatial clustering)",
                    'recommendation': f"Inspect Wafer {top_wafer} for physical defects. Check fab process uniformity.",
                    'confidence': 0.8
                })
        
        # Sort by severity and confidence
        analysis['root_causes'].sort(key=lambda x: (
            {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}[x['severity']],
            x['confidence']
        ), reverse=True)
        
        self.analysis_results = analysis
        return analysis
    
    def generate_rca_report(self) -> str:
        """
        Generate formatted RCA report
        
        Returns:
            Markdown-formatted report
        """
        if self.analysis_results is None:
            return "No analysis performed. Call analyze_failures() first."
        
        analysis = self.analysis_results
        
        report = []
        report.append("# 🔍 Root Cause Analysis Report")
        report.append("")
        report.append(f"**Failure Count:** {analysis['failure_count']}")
        report.append(f"**Failure Rate:** {analysis['failure_rate']:.2f}%")
        report.append("")
        
        if len(analysis['root_causes']) == 0:
            report.append("✅ No specific root causes identified. Failures appear random.")
        else:
            report.append("## Identified Root Causes")
            report.append("")
            
            for i, cause in enumerate(analysis['root_causes'], 1):
                report.append(f"### {i}. {cause['category']} [**{cause['severity']}**]")
                report.append(f"**Confidence:** {cause['confidence']*100:.0f}%")
                report.append("")
                report.append(f"**Description:** {cause['description']}")
                report.append("")
                report.append(f"**Recommendation:** {cause['recommendation']}")
                report.append("")
        
        return "\n".join(report)


class ModelExplainer:
    """
    Model Explainability using SHAP and LIME
    
    Provides interpretability for ML models to understand
    which features drive predictions.
    """
    
    def __init__(self, model, X_train: np.ndarray, feature_names: List[str]):
        """
        Initialize explainer
        
        Args:
            model: Trained model (scikit-learn compatible)
            X_train: Training data for background
            feature_names: Names of features
        """
        self.model = model
        self.X_train = X_train
        self.feature_names = feature_names
        self.shap_explainer = None
        self.lime_explainer = None
        
    def explain_with_shap(self, X_test: np.ndarray, max_display: int = 10) -> Dict:
        """
        Generate SHAP explanations
        
        Args:
            X_test: Test data to explain
            max_display: Maximum features to display
            
        Returns:
            Dictionary with SHAP values and summary
        """
        try:
            # Initialize SHAP explainer
            if self.shap_explainer is None:
                self.shap_explainer = shap.Explainer(self.model, self.X_train)
            
            # Calculate SHAP values
            shap_values = self.shap_explainer(X_test)
            
            # Global feature importance
            mean_abs_shap = np.abs(shap_values.values).mean(axis=0)
            importance_df = pd.DataFrame({
                'feature': self.feature_names,
                'importance': mean_abs_shap
            }).sort_values('importance', ascending=False)
            
            return {
                'shap_values': shap_values,
                'feature_importance': importance_df,
                'explainer': self.shap_explainer
            }
            
        except Exception as e:
            logger.error(f"SHAP explanation failed: {e}")
            return {'error': str(e)}
    
    def explain_with_lime(self, X_instance: np.ndarray, num_features: int = 10) -> Dict:
        """
        Generate LIME explanation for a single instance
        
        Args:
            X_instance: Single instance to explain
            num_features: Number of top features to show
            
        Returns:
            Dictionary with LIME explanation
        """
        try:
            # Initialize LIME explainer
            if self.lime_explainer is None:
                self.lime_explainer = lime_tabular.LimeTabularExplainer(
                    self.X_train,
                    feature_names=self.feature_names,
                    class_names=['FAIL', 'PASS'],
                    mode='classification'
                )
            
            # Explain instance
            explanation = self.lime_explainer.explain_instance(
                X_instance.flatten(),
                self.model.predict_proba,
                num_features=num_features
            )
            
            # Extract feature contributions
            feature_weights = explanation.as_list()
            
            return {
                'explanation': explanation,
                'feature_weights': feature_weights,
                'predicted_class': self.model.predict([X_instance])[0],
                'probability': self.model.predict_proba([X_instance])[0]
            }
            
        except Exception as e:
            logger.error(f"LIME explanation failed: {e}")
            return {'error': str(e)}
    
    def plot_shap_summary(self, shap_values, max_display: int = 10) -> go.Figure:
        """
        Create SHAP summary plot
        
        Args:
            shap_values: SHAP values from explain_with_shap
            max_display: Maximum features to display
            
        Returns:
            Plotly figure
        """
        # Calculate mean absolute SHAP values
        mean_abs_shap = np.abs(shap_values.values).mean(axis=0)
        
        # Sort features by importance
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': mean_abs_shap
        }).sort_values('importance', ascending=True).tail(max_display)
        
        # Create bar plot
        fig = go.Figure(go.Bar(
            x=feature_importance['importance'],
            y=feature_importance['feature'],
            orientation='h',
            marker=dict(color=feature_importance['importance'], colorscale='Viridis')
        ))
        
        fig.update_layout(
            title='SHAP Feature Importance',
            xaxis_title='Mean |SHAP Value|',
            yaxis_title='Feature',
            template='plotly_white',
            height=500
        )
        
        return fig


class RecommendationEngine:
    """
    Intelligent Recommendation System
    
    Generates actionable recommendations based on analysis results.
    """
    
    def __init__(self):
        """Initialize recommendation engine"""
        self.rules = self._load_rules()
        
    def _load_rules(self) -> List[Dict]:
        """Load recommendation rules"""
        return [
            {
                'condition': lambda m: m.get('yield', 100) < 90,
                'recommendation': "⚠️ Yield below 90% - Immediate action required. Review test parameters and equipment calibration.",
                'priority': 'HIGH'
            },
            {
                'condition': lambda m: m.get('test_time_avg', 0) > 100,
                'recommendation': "⏱️ Average test time exceeds 100ms - Optimize test sequence or consider parallel testing.",
                'priority': 'MEDIUM'
            },
            {
                'condition': lambda m: m.get('anomaly_rate', 0) > 5,
                'recommendation': "🔍 High anomaly rate (>5%) - Investigate outliers and consider process adjustments.",
                'priority': 'HIGH'
            },
            {
                'condition': lambda m: m.get('trend', '') == 'declining',
                'recommendation': "📉 Declining trend detected - Monitor closely and identify root cause before further degradation.",
                'priority': 'MEDIUM'
            },
            {
                'condition': lambda m: m.get('correlation_found', False),
                'recommendation': "🔗 Strong correlations detected - Leverage correlated tests for early prediction.",
                'priority': 'LOW'
            }
        ]
    
    def generate_recommendations(self, metrics: Dict) -> List[Dict]:
        """
        Generate recommendations based on metrics
        
        Args:
            metrics: Analysis metrics dictionary
            
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        for rule in self.rules:
            try:
                if rule['condition'](metrics):
                    recommendations.append({
                        'recommendation': rule['recommendation'],
                        'priority': rule['priority'],
                        'timestamp': datetime.now().isoformat()
                    })
            except Exception as e:
                logger.debug(f"Rule evaluation failed: {e}")
        
        # Sort by priority
        priority_order = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
        recommendations.sort(key=lambda x: priority_order[x['priority']], reverse=True)
        
        return recommendations


if __name__ == "__main__":
    print("AI-Powered Insights Module")
    print("=" * 60)
    print("✅ Insight Generator - Natural Language Generation")
    print("✅ Root Cause Analyzer - Automated RCA")
    print("✅ Model Explainer - SHAP & LIME")
    print("✅ Recommendation Engine - Intelligent suggestions")
