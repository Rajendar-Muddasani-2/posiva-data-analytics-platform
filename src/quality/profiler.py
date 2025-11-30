"""
Data Quality Module
Automated data profiling and quality checks
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataProfiler:
    """
    Automated data profiling and quality assessment
    """
    
    def __init__(self):
        self.logger = logger
        self.profile_results = {}
    
    def profile(self, df: pd.DataFrame, name: str = "dataset") -> Dict:
        """
        Generate comprehensive data profile
        
        Args:
            df: DataFrame to profile
            name: Dataset name
            
        Returns:
            Profile dictionary
        """
        self.logger.info(f"Profiling dataset: {name}")
        
        profile = {
            'name': name,
            'overview': self._profile_overview(df),
            'columns': self._profile_columns(df),
            'missing_values': self._analyze_missing(df),
            'duplicates': self._analyze_duplicates(df),
            'correlations': self._analyze_correlations(df),
            'quality_score': 0.0
        }
        
        # Calculate overall quality score
        profile['quality_score'] = self._calculate_quality_score(profile)
        
        self.profile_results[name] = profile
        self.logger.info(f"Profile complete. Quality score: {profile['quality_score']:.1f}%")
        
        return profile
    
    def _profile_overview(self, df: pd.DataFrame) -> Dict:
        """Basic dataset overview"""
        return {
            'rows': len(df),
            'columns': len(df.columns),
            'memory_mb': df.memory_usage(deep=True).sum() / 1024**2,
            'dtypes': df.dtypes.value_counts().to_dict()
        }
    
    def _profile_columns(self, df: pd.DataFrame) -> Dict:
        """Profile each column"""
        column_profiles = {}
        
        for col in df.columns:
            col_profile = {
                'dtype': str(df[col].dtype),
                'missing': int(df[col].isnull().sum()),
                'missing_pct': float(df[col].isnull().sum() / len(df) * 100),
                'unique': int(df[col].nunique()),
                'unique_pct': float(df[col].nunique() / len(df) * 100),
            }
            
            # Numeric columns
            if pd.api.types.is_numeric_dtype(df[col]):
                col_profile.update({
                    'mean': float(df[col].mean()) if not df[col].isnull().all() else None,
                    'std': float(df[col].std()) if not df[col].isnull().all() else None,
                    'min': float(df[col].min()) if not df[col].isnull().all() else None,
                    'max': float(df[col].max()) if not df[col].isnull().all() else None,
                    'median': float(df[col].median()) if not df[col].isnull().all() else None,
                    'zeros': int((df[col] == 0).sum()),
                    'negatives': int((df[col] < 0).sum()),
                })
            
            # String columns
            elif pd.api.types.is_string_dtype(df[col]) or pd.api.types.is_object_dtype(df[col]):
                col_profile.update({
                    'top_values': df[col].value_counts().head(5).to_dict(),
                })
            
            column_profiles[col] = col_profile
        
        return column_profiles
    
    def _analyze_missing(self, df: pd.DataFrame) -> Dict:
        """Analyze missing values"""
        missing = df.isnull().sum()
        missing_pct = (missing / len(df) * 100).round(2)
        
        return {
            'total_missing': int(missing.sum()),
            'columns_with_missing': int((missing > 0).sum()),
            'by_column': {
                col: {'count': int(missing[col]), 'percentage': float(missing_pct[col])}
                for col in df.columns if missing[col] > 0
            }
        }
    
    def _analyze_duplicates(self, df: pd.DataFrame) -> Dict:
        """Analyze duplicate rows"""
        duplicates = df.duplicated()
        return {
            'count': int(duplicates.sum()),
            'percentage': float(duplicates.sum() / len(df) * 100)
        }
    
    def _analyze_correlations(self, df: pd.DataFrame) -> Dict:
        """Analyze correlations for numeric columns"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) < 2:
            return {'message': 'Not enough numeric columns'}
        
        corr_matrix = df[numeric_cols].corr()
        
        # Find high correlations (>0.8 or <-0.8)
        high_corr = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) > 0.8:
                    high_corr.append({
                        'col1': corr_matrix.columns[i],
                        'col2': corr_matrix.columns[j],
                        'correlation': float(corr_val)
                    })
        
        return {
            'high_correlations': high_corr,
            'correlation_matrix_shape': corr_matrix.shape
        }
    
    def _calculate_quality_score(self, profile: Dict) -> float:
        """Calculate overall quality score (0-100)"""
        scores = []
        
        # Completeness score (penalize missing values)
        missing_pct = sum(
            col_data['missing_pct'] 
            for col_data in profile['columns'].values()
        ) / len(profile['columns'])
        completeness = max(0, 100 - missing_pct)
        scores.append(completeness)
        
        # Duplicate score (penalize duplicates)
        duplicate_pct = profile['duplicates']['percentage']
        duplicate_score = max(0, 100 - duplicate_pct * 10)
        scores.append(duplicate_score)
        
        # Uniqueness score (columns should have reasonable uniqueness)
        uniqueness_scores = []
        for col_data in profile['columns'].values():
            if col_data['unique_pct'] > 0:
                uniqueness_scores.append(min(100, col_data['unique_pct'] * 2))
        if uniqueness_scores:
            scores.append(np.mean(uniqueness_scores))
        
        return float(np.mean(scores))
    
    def generate_report(self, profile: Dict) -> str:
        """Generate text report from profile"""
        report = []
        report.append("=" * 60)
        report.append(f"DATA QUALITY REPORT: {profile['name']}")
        report.append("=" * 60)
        
        # Overview
        overview = profile['overview']
        report.append(f"\n📊 OVERVIEW:")
        report.append(f"   Rows: {overview['rows']:,}")
        report.append(f"   Columns: {overview['columns']}")
        report.append(f"   Memory: {overview['memory_mb']:.2f} MB")
        report.append(f"   Quality Score: {profile['quality_score']:.1f}/100")
        
        # Missing values
        missing = profile['missing_values']
        report.append(f"\n❌ MISSING VALUES:")
        report.append(f"   Total: {missing['total_missing']:,}")
        report.append(f"   Columns affected: {missing['columns_with_missing']}")
        if missing['by_column']:
            report.append("   Top columns:")
            for col, data in list(missing['by_column'].items())[:5]:
                report.append(f"      - {col}: {data['count']:,} ({data['percentage']:.1f}%)")
        
        # Duplicates
        dup = profile['duplicates']
        report.append(f"\n🔄 DUPLICATES:")
        report.append(f"   Count: {dup['count']:,} ({dup['percentage']:.2f}%)")
        
        # Correlations
        corr = profile['correlations']
        if 'high_correlations' in corr and corr['high_correlations']:
            report.append(f"\n🔗 HIGH CORRELATIONS:")
            for item in corr['high_correlations'][:5]:
                report.append(f"   {item['col1']} <-> {item['col2']}: {item['correlation']:.3f}")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)
    
    def save_report(self, profile: Dict, output_path: Path):
        """Save report to file"""
        report = self.generate_report(profile)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(report)
        
        self.logger.info(f"Report saved to {output_path}")


class DataValidator:
    """
    Data validation with custom rules
    """
    
    def __init__(self):
        self.logger = logger
        self.validation_results = []
    
    def validate(self, df: pd.DataFrame, rules: Dict) -> List[Dict]:
        """
        Validate DataFrame against rules
        
        Args:
            df: DataFrame to validate
            rules: Validation rules dictionary
            
        Returns:
            List of validation results
        """
        self.logger.info("Starting validation...")
        results = []
        
        # Required columns check
        if 'required_columns' in rules:
            results.append(self._check_required_columns(df, rules['required_columns']))
        
        # Column type checks
        if 'column_types' in rules:
            results.append(self._check_column_types(df, rules['column_types']))
        
        # Value range checks
        if 'value_ranges' in rules:
            for col, range_rule in rules['value_ranges'].items():
                results.append(self._check_value_range(df, col, range_rule))
        
        # Custom checks
        if 'custom_checks' in rules:
            for check_name, check_func in rules['custom_checks'].items():
                results.append(self._run_custom_check(df, check_name, check_func))
        
        self.validation_results = results
        
        passed = sum(1 for r in results if r['passed'])
        self.logger.info(f"Validation complete: {passed}/{len(results)} checks passed")
        
        return results
    
    def _check_required_columns(self, df: pd.DataFrame, required: List[str]) -> Dict:
        """Check for required columns"""
        missing = set(required) - set(df.columns)
        return {
            'check': 'required_columns',
            'passed': len(missing) == 0,
            'message': f"Missing columns: {missing}" if missing else "All required columns present",
            'missing_columns': list(missing)
        }
    
    def _check_column_types(self, df: pd.DataFrame, type_rules: Dict) -> Dict:
        """Check column data types"""
        mismatches = []
        for col, expected_type in type_rules.items():
            if col in df.columns:
                actual_type = df[col].dtype
                if not self._types_match(actual_type, expected_type):
                    mismatches.append(f"{col}: expected {expected_type}, got {actual_type}")
        
        return {
            'check': 'column_types',
            'passed': len(mismatches) == 0,
            'message': "; ".join(mismatches) if mismatches else "All types correct",
            'mismatches': mismatches
        }
    
    def _check_value_range(self, df: pd.DataFrame, col: str, range_rule: Dict) -> Dict:
        """Check value ranges"""
        if col not in df.columns:
            return {
                'check': f'value_range_{col}',
                'passed': False,
                'message': f"Column {col} not found"
            }
        
        violations = 0
        if 'min' in range_rule:
            violations += (df[col] < range_rule['min']).sum()
        if 'max' in range_rule:
            violations += (df[col] > range_rule['max']).sum()
        
        return {
            'check': f'value_range_{col}',
            'passed': violations == 0,
            'message': f"{violations} values out of range" if violations > 0 else "All values in range",
            'violations': int(violations)
        }
    
    def _run_custom_check(self, df: pd.DataFrame, name: str, check_func) -> Dict:
        """Run custom validation function"""
        try:
            result = check_func(df)
            return {
                'check': f'custom_{name}',
                'passed': bool(result),
                'message': "Custom check passed" if result else "Custom check failed"
            }
        except Exception as e:
            return {
                'check': f'custom_{name}',
                'passed': False,
                'message': f"Error: {str(e)}"
            }
    
    @staticmethod
    def _types_match(actual, expected) -> bool:
        """Check if types match (flexible matching)"""
        type_map = {
            'int': ['int', 'int64', 'int32'],
            'float': ['float', 'float64', 'float32'],
            'string': ['object', 'string'],
            'bool': ['bool'],
        }
        
        actual_str = str(actual)
        expected_str = str(expected)
        
        for key, values in type_map.items():
            if expected_str in [key] + values:
                return any(v in actual_str for v in [key] + values)
        
        return actual_str == expected_str
