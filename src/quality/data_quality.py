# Adapter providing test-compatible DataQualityChecker interface
import pandas as pd


class DataQualityChecker:
    """Lightweight quality checker accepting df in constructor."""

    def __init__(self, df: pd.DataFrame):
        self._df = df

    def quality_score(self) -> float:
        """0-100 completeness score (100 = no missing values)."""
        total_cells = len(self._df) * len(self._df.columns)
        if total_cells == 0:
            return 100.0
        missing = self._df.isnull().sum().sum()
        return round(max(0.0, 100.0 - (missing / total_cells * 100)), 2)

    def missing_values(self) -> pd.Series:
        """Per-column missing-value counts."""
        return self._df.isnull().sum()

    def duplicate_count(self) -> int:
        return int(self._df.duplicated().sum())
