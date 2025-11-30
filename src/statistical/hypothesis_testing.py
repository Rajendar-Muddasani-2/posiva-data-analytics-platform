"""
Statistical Analysis Module
Hypothesis testing, correlation, and statistical methods
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy import stats
from scipy.stats import chi2_contingency, pearsonr, spearmanr
import plotly.graph_objects as go
import plotly.express as px
from src.utils.logger import get_logger

logger = get_logger(__name__)


class StatisticalAnalysis:
    """
    Statistical hypothesis testing and analysis
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with DataFrame
        
        Args:
            df: DataFrame with test results
        """
        self.df = df
        self.logger = logger
    
    def t_test(self, group_col: str, value_col: str, group1: str, group2: str) -> Dict:
        """
        Perform independent samples t-test
        
        Args:
            group_col: Column name for groups
            value_col: Column name for values
            group1: First group value
            group2: Second group value
            
        Returns:
            Dictionary with test results
        """
        data1 = self.df[self.df[group_col] == group1][value_col].dropna()
        data2 = self.df[self.df[group_col] == group2][value_col].dropna()
        
        if len(data1) < 2 or len(data2) < 2:
            return {'error': 'Insufficient data'}
        
        # Perform t-test
        t_stat, p_value = stats.ttest_ind(data1, data2)
        
        # Calculate effect size (Cohen's d)
        pooled_std = np.sqrt((data1.std()**2 + data2.std()**2) / 2)
        cohens_d = (data1.mean() - data2.mean()) / pooled_std if pooled_std > 0 else 0
        
        return {
            'test': 't-test',
            'group1': group1,
            'group2': group2,
            'n1': len(data1),
            'n2': len(data2),
            'mean1': float(data1.mean()),
            'mean2': float(data2.mean()),
            'std1': float(data1.std()),
            'std2': float(data2.std()),
            't_statistic': float(t_stat),
            'p_value': float(p_value),
            'significant': bool(p_value < 0.05),
            'cohens_d': float(cohens_d),
            'effect_size': 'large' if abs(cohens_d) >= 0.8 else 'medium' if abs(cohens_d) >= 0.5 else 'small'
        }
    
    def anova(self, group_col: str, value_col: str) -> Dict:
        """
        Perform one-way ANOVA
        
        Args:
            group_col: Column name for groups
            value_col: Column name for values
            
        Returns:
            Dictionary with ANOVA results
        """
        groups = []
        group_names = self.df[group_col].unique()
        
        for group in group_names:
            data = self.df[self.df[group_col] == group][value_col].dropna()
            if len(data) >= 2:
                groups.append(data)
        
        if len(groups) < 2:
            return {'error': 'Insufficient groups'}
        
        # Perform ANOVA
        f_stat, p_value = stats.f_oneway(*groups)
        
        # Calculate eta squared (effect size)
        grand_mean = self.df[value_col].mean()
        ss_between = sum(len(g) * (g.mean() - grand_mean)**2 for g in groups)
        ss_total = sum((self.df[value_col] - grand_mean)**2)
        eta_squared = ss_between / ss_total if ss_total > 0 else 0
        
        return {
            'test': 'ANOVA',
            'groups': len(groups),
            'group_names': list(group_names[:len(groups)]),
            'f_statistic': float(f_stat),
            'p_value': float(p_value),
            'significant': bool(p_value < 0.05),
            'eta_squared': float(eta_squared),
            'effect_size': 'large' if eta_squared >= 0.14 else 'medium' if eta_squared >= 0.06 else 'small'
        }
    
    def chi_square_test(self, col1: str, col2: str) -> Dict:
        """
        Perform chi-square test of independence
        
        Args:
            col1: First categorical column
            col2: Second categorical column
            
        Returns:
            Dictionary with chi-square test results
        """
        contingency_table = pd.crosstab(self.df[col1], self.df[col2])
        
        chi2, p_value, dof, expected = chi2_contingency(contingency_table)
        
        # Calculate Cramér's V (effect size)
        n = contingency_table.sum().sum()
        min_dim = min(contingency_table.shape) - 1
        cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 and n > 0 else 0
        
        return {
            'test': 'Chi-Square',
            'variable1': col1,
            'variable2': col2,
            'chi2_statistic': float(chi2),
            'p_value': float(p_value),
            'degrees_of_freedom': int(dof),
            'significant': bool(p_value < 0.05),
            'cramers_v': float(cramers_v),
            'effect_size': 'large' if cramers_v >= 0.5 else 'medium' if cramers_v >= 0.3 else 'small'
        }
    
    def correlation_test(self, col1: str, col2: str, method: str = 'pearson') -> Dict:
        """
        Test correlation between two variables
        
        Args:
            col1: First numeric column
            col2: Second numeric column
            method: 'pearson' or 'spearman'
            
        Returns:
            Dictionary with correlation results
        """
        data = self.df[[col1, col2]].dropna()
        
        if len(data) < 3:
            return {'error': 'Insufficient data'}
        
        if method == 'pearson':
            corr, p_value = pearsonr(data[col1], data[col2])
        elif method == 'spearman':
            corr, p_value = spearmanr(data[col1], data[col2])
        else:
            raise ValueError("method must be 'pearson' or 'spearman'")
        
        # Interpret strength
        abs_corr = abs(corr)
        if abs_corr >= 0.7:
            strength = 'strong'
        elif abs_corr >= 0.4:
            strength = 'moderate'
        elif abs_corr >= 0.2:
            strength = 'weak'
        else:
            strength = 'very weak'
        
        return {
            'test': f'{method.capitalize()} Correlation',
            'variable1': col1,
            'variable2': col2,
            'n': len(data),
            'correlation': float(corr),
            'p_value': float(p_value),
            'significant': bool(p_value < 0.05),
            'strength': strength,
            'direction': 'positive' if corr > 0 else 'negative'
        }
    
    def normality_test(self, col: str) -> Dict:
        """
        Test for normal distribution
        
        Args:
            col: Column name
            
        Returns:
            Dictionary with normality test results
        """
        data = self.df[col].dropna()
        
        if len(data) < 3:
            return {'error': 'Insufficient data'}
        
        # Shapiro-Wilk test (for n <= 5000)
        if len(data) <= 5000:
            shapiro_stat, shapiro_p = stats.shapiro(data)
        else:
            shapiro_stat, shapiro_p = None, None
        
        # Kolmogorov-Smirnov test
        ks_stat, ks_p = stats.kstest(data, 'norm', args=(data.mean(), data.std()))
        
        # Calculate skewness and kurtosis
        skewness = stats.skew(data)
        kurtosis = stats.kurtosis(data)
        
        return {
            'test': 'Normality Tests',
            'variable': col,
            'n': len(data),
            'mean': float(data.mean()),
            'std': float(data.std()),
            'shapiro_statistic': float(shapiro_stat) if shapiro_stat else None,
            'shapiro_pvalue': float(shapiro_p) if shapiro_p else None,
            'ks_statistic': float(ks_stat),
            'ks_pvalue': float(ks_p),
            'skewness': float(skewness),
            'kurtosis': float(kurtosis),
            'is_normal': bool(ks_p > 0.05),
            'interpretation': 'Normal' if ks_p > 0.05 else 'Not Normal'
        }
    
    def confidence_interval(self, col: str, confidence: float = 0.95) -> Dict:
        """
        Calculate confidence interval for mean
        
        Args:
            col: Column name
            confidence: Confidence level (default 0.95)
            
        Returns:
            Dictionary with confidence interval
        """
        data = self.df[col].dropna()
        
        if len(data) < 2:
            return {'error': 'Insufficient data'}
        
        mean = data.mean()
        sem = stats.sem(data)  # Standard error of mean
        ci = stats.t.interval(confidence, len(data)-1, loc=mean, scale=sem)
        
        return {
            'variable': col,
            'n': len(data),
            'mean': float(mean),
            'std': float(data.std()),
            'sem': float(sem),
            'confidence_level': confidence,
            'lower_bound': float(ci[0]),
            'upper_bound': float(ci[1]),
            'margin_of_error': float(ci[1] - mean)
        }
    
    def mann_whitney_u_test(self, group_col: str, value_col: str, group1: str, group2: str) -> Dict:
        """
        Perform Mann-Whitney U test (non-parametric alternative to t-test)
        
        Args:
            group_col: Column name for groups
            value_col: Column name for values
            group1: First group value
            group2: Second group value
            
        Returns:
            Dictionary with test results
        """
        data1 = self.df[self.df[group_col] == group1][value_col].dropna()
        data2 = self.df[self.df[group_col] == group2][value_col].dropna()
        
        if len(data1) < 2 or len(data2) < 2:
            return {'error': 'Insufficient data'}
        
        # Perform Mann-Whitney U test
        u_stat, p_value = stats.mannwhitneyu(data1, data2, alternative='two-sided')
        
        return {
            'test': 'Mann-Whitney U',
            'group1': group1,
            'group2': group2,
            'n1': len(data1),
            'n2': len(data2),
            'median1': float(data1.median()),
            'median2': float(data2.median()),
            'u_statistic': float(u_stat),
            'p_value': float(p_value),
            'significant': bool(p_value < 0.05)
        }
    
    def kruskal_wallis_test(self, group_col: str, value_col: str) -> Dict:
        """
        Perform Kruskal-Wallis H test (non-parametric alternative to ANOVA)
        
        Args:
            group_col: Column name for groups
            value_col: Column name for values
            
        Returns:
            Dictionary with test results
        """
        groups = []
        group_names = self.df[group_col].unique()
        
        for group in group_names:
            data = self.df[self.df[group_col] == group][value_col].dropna()
            if len(data) >= 2:
                groups.append(data)
        
        if len(groups) < 2:
            return {'error': 'Insufficient groups'}
        
        # Perform Kruskal-Wallis test
        h_stat, p_value = stats.kruskal(*groups)
        
        return {
            'test': 'Kruskal-Wallis H',
            'groups': len(groups),
            'group_names': list(group_names[:len(groups)]),
            'h_statistic': float(h_stat),
            'p_value': float(p_value),
            'significant': bool(p_value < 0.05)
        }
    
    def generate_summary_report(self) -> str:
        """Generate comprehensive statistical summary"""
        report = []
        report.append("=" * 60)
        report.append("STATISTICAL ANALYSIS SUMMARY")
        report.append("=" * 60)
        
        # Basic statistics
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        report.append(f"\nNumeric Variables: {len(numeric_cols)}")
        
        for col in numeric_cols[:5]:  # Show first 5
            report.append(f"\n{col}:")
            report.append(f"  Mean: {self.df[col].mean():.2f}")
            report.append(f"  Median: {self.df[col].median():.2f}")
            report.append(f"  Std: {self.df[col].std():.2f}")
            
            # Normality
            if len(self.df[col].dropna()) >= 3:
                norm_test = self.normality_test(col)
                report.append(f"  Normal: {norm_test['is_normal']}")
        
        return "\n".join(report)
