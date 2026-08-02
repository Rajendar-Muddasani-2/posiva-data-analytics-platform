# Adapter providing test-compatible TestTimeAnalyzer interface
from src.analytics.test_time_analytics import TestTimeAnalytics


class TestTimeAnalyzer:
    """Adapts TestTimeAnalytics with normalized column names and test-compatible methods."""

    _TIME_COLS = ["test_time_sec", "Test_Time_sec", "TEST_TIME_SEC",
                  "test_time", "Test_Time", "duration"]

    def __init__(self, df):
        self._df = df.copy()
        self._time_col = next(
            (c for c in self._TIME_COLS if c in self._df.columns), None
        ) or self._df.select_dtypes("number").columns[0]

    def statistics(self):
        s = self._df[self._time_col]
        return {
            "mean":   float(s.mean()),
            "median": float(s.median()),
            "std":    float(s.std()),
            "min":    float(s.min()),
            "max":    float(s.max()),
        }

    def overall_statistics(self):
        return self.statistics()
