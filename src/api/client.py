"""
API client for POSIVA Analytics Platform
"""

import requests
from typing import Dict, List, Optional
import pandas as pd
from io import StringIO

class PosivaClient:
    """Client for POSIVA Analytics API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize client
        
        Args:
            base_url: Base URL of API server
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def health(self) -> Dict:
        """Check API health"""
        response = self.session.get(f"{self.base_url}/api/health")
        response.raise_for_status()
        return response.json()
    
    def get_yield_analytics(self) -> Dict:
        """Get overall yield analytics"""
        response = self.session.get(f"{self.base_url}/api/analytics/yield")
        response.raise_for_status()
        return response.json()
    
    def get_yield_by_test(self) -> pd.DataFrame:
        """Get yield analytics by test"""
        response = self.session.get(f"{self.base_url}/api/analytics/by-test")
        response.raise_for_status()
        return pd.DataFrame(response.json())
    
    def get_yield_by_lot(self) -> pd.DataFrame:
        """Get yield analytics by lot"""
        response = self.session.get(f"{self.base_url}/api/analytics/by-lot")
        response.raise_for_status()
        return pd.DataFrame(response.json())
    
    def predict_yield(
        self,
        test_time: float,
        test_result: str,
        wafer_id: str,
        lot_id: str
    ) -> Dict:
        """
        Predict device yield
        
        Args:
            test_time: Test time in seconds
            test_result: Test name
            wafer_id: Wafer ID
            lot_id: Lot ID
        
        Returns:
            Prediction result with confidence
        """
        payload = {
            "test_time": test_time,
            "test_result": test_result,
            "wafer_id": wafer_id,
            "lot_id": lot_id
        }
        response = self.session.post(
            f"{self.base_url}/api/predict/yield",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def predict_batch(self, file_path: str) -> pd.DataFrame:
        """
        Batch predictions from CSV file
        
        Args:
            file_path: Path to CSV file
        
        Returns:
            DataFrame with predictions
        """
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = self.session.post(
                f"{self.base_url}/api/predict/batch",
                files=files
            )
        response.raise_for_status()
        return pd.DataFrame(response.json())
    
    def create_forecast(
        self,
        metric: str,
        periods: int = 10,
        method: str = "prophet"
    ) -> Dict:
        """
        Create time series forecast
        
        Args:
            metric: Metric to forecast (yield, test_time)
            periods: Number of periods
            method: Forecasting method (prophet, arima)
        
        Returns:
            Forecast results
        """
        payload = {
            "metric": metric,
            "periods": periods,
            "method": method
        }
        response = self.session.post(
            f"{self.base_url}/api/forecast",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def generate_insights(self) -> Dict:
        """Generate AI-powered insights"""
        response = self.session.get(f"{self.base_url}/api/insights/generate")
        response.raise_for_status()
        return response.json()
    
    def root_cause_analysis(self) -> Dict:
        """Perform root cause analysis"""
        response = self.session.get(f"{self.base_url}/api/insights/rca")
        response.raise_for_status()
        return response.json()
    
    def train_model(self, model_type: str = "random_forest") -> Dict:
        """
        Train ML model
        
        Args:
            model_type: Type of model to train
        
        Returns:
            Training status
        """
        response = self.session.post(
            f"{self.base_url}/api/model/train",
            params={"model_type": model_type}
        )
        response.raise_for_status()
        return response.json()
    
    def get_model_metrics(self) -> Dict:
        """Get trained model metrics"""
        response = self.session.get(f"{self.base_url}/api/model/metrics")
        response.raise_for_status()
        return response.json()
    
    def export_data(self, format: str = "csv") -> pd.DataFrame:
        """
        Export data
        
        Args:
            format: Export format (csv, json)
        
        Returns:
            Exported data as DataFrame
        """
        response = self.session.get(
            f"{self.base_url}/api/export/data",
            params={"format": format}
        )
        response.raise_for_status()
        
        if format == "csv":
            return pd.read_csv(StringIO(response.json()['data']))
        else:
            return pd.DataFrame(response.json())


# Example usage
if __name__ == "__main__":
    # Initialize client
    client = PosivaClient()
    
    # Check health
    print("API Health:", client.health())
    
    # Get yield analytics
    print("\nYield Analytics:", client.get_yield_analytics())
    
    # Make prediction
    prediction = client.predict_yield(
        test_time=2.5,
        test_result="CONT_TEST",
        wafer_id="W001",
        lot_id="L001"
    )
    print("\nPrediction:", prediction)
    
    # Generate insights
    insights = client.generate_insights()
    print("\nInsights:", insights['insights'][0])
