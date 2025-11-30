"""
FastAPI REST API for POSIVA Analytics Platform

Provides programmatic access to analytics, predictions, and reporting.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import io
import logging

# Import POSIVA modules
import sys
sys.path.append('.')
from src.analytics.yield_analytics import YieldAnalyzer
from src.ml.ml_models import YieldPredictionModel
from src.statistical.forecasting import ProphetForecaster, ARIMAForecaster
from src.ai.insights import InsightGenerator, RootCauseAnalyzer, RecommendationEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="POSIVA Analytics API",
    description="REST API for semiconductor manufacturing analytics",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class PredictionRequest(BaseModel):
    test_time: float = Field(..., description="Test time in seconds")
    test_result: str = Field(..., description="Test name")
    wafer_id: str = Field(..., description="Wafer ID")
    lot_id: str = Field(..., description="Lot ID")

class PredictionResponse(BaseModel):
    prediction: str = Field(..., description="PASS or FAIL")
    confidence: float = Field(..., description="Prediction confidence (0-1)")
    risk_score: float = Field(..., description="Risk score (0-1)")

class ForecastRequest(BaseModel):
    metric: str = Field(..., description="Metric to forecast (yield, test_time)")
    periods: int = Field(10, description="Number of periods to forecast")
    method: str = Field("prophet", description="Forecasting method (prophet, arima)")

class AnalyticsResponse(BaseModel):
    overall_yield: float
    total_devices: int
    pass_count: int
    fail_count: int
    top_failing_tests: List[Dict]
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str

# Global state (in production, use proper state management)
trained_models = {}
data_cache = None

# Helper functions
def load_data():
    """Load data from file"""
    global data_cache
    if data_cache is None:
        try:
            data_cache = pd.read_csv('data/sample_data.csv')
            logger.info(f"Loaded {len(data_cache)} records from data file")
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            data_cache = pd.DataFrame()
    return data_cache

# API Endpoints

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/analytics/yield", response_model=AnalyticsResponse)
async def get_yield_analytics():
    """Get overall yield analytics"""
    try:
        df = load_data()
        if df.empty:
            raise HTTPException(status_code=500, detail="No data available")
        
        analyzer = YieldAnalyzer(df)
        overall = analyzer.overall_yield()
        by_test = analyzer.yield_by_test()
        
        top_failing = by_test.nsmallest(5, 'Yield %')[['Test', 'Yield %', 'Fail Count']].to_dict('records')
        
        return {
            "overall_yield": overall['Yield %'],
            "total_devices": int(overall['Total Devices']),
            "pass_count": int(overall['Pass Count']),
            "fail_count": int(overall['Fail Count']),
            "top_failing_tests": top_failing,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in yield analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/by-test")
async def get_yield_by_test():
    """Get yield analytics by test"""
    try:
        df = load_data()
        analyzer = YieldAnalyzer(df)
        by_test = analyzer.yield_by_test()
        return by_test.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/by-lot")
async def get_yield_by_lot():
    """Get yield analytics by lot"""
    try:
        df = load_data()
        analyzer = YieldAnalyzer(df)
        by_lot = analyzer.yield_by_lot()
        return by_lot.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/predict/yield", response_model=PredictionResponse)
async def predict_yield(request: PredictionRequest):
    """Predict device yield"""
    try:
        # Load or train model
        if 'yield_model' not in trained_models:
            df = load_data()
            model = YieldPredictionModel()
            model.train(df)
            trained_models['yield_model'] = model
        
        model = trained_models['yield_model']
        
        # Create prediction dataframe
        pred_df = pd.DataFrame([{
            'Test_Time_sec': request.test_time,
            'Test_Result': request.test_result,
            'Wafer_ID': request.wafer_id,
            'Lot_ID': request.lot_id
        }])
        
        # Make prediction
        prediction = model.predict(pred_df)[0]
        probabilities = model.predict_proba(pred_df)[0]
        confidence = float(max(probabilities))
        risk_score = float(probabilities[0]) if prediction == 'FAIL' else float(probabilities[1])
        
        return {
            "prediction": prediction,
            "confidence": confidence,
            "risk_score": 1.0 - confidence
        }
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/predict/batch")
async def predict_batch(file: UploadFile = File(...)):
    """Batch prediction from CSV file"""
    try:
        # Read uploaded file
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Load or train model
        if 'yield_model' not in trained_models:
            data_df = load_data()
            model = YieldPredictionModel()
            model.train(data_df)
            trained_models['yield_model'] = model
        
        model = trained_models['yield_model']
        
        # Make predictions
        predictions = model.predict(df)
        probabilities = model.predict_proba(df)
        
        # Add predictions to dataframe
        df['Prediction'] = predictions
        df['Confidence'] = probabilities.max(axis=1)
        
        # Convert to JSON
        return df.to_dict('records')
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/forecast")
async def create_forecast(request: ForecastRequest):
    """Create time series forecast"""
    try:
        df = load_data()
        
        # Prepare time series data
        if 'Date' not in df.columns:
            # Add synthetic dates if not present
            df['Date'] = pd.date_range(start='2023-01-01', periods=len(df), freq='D')
        
        if request.metric == 'yield':
            # Calculate daily yield
            ts_data = df.groupby('Date')['Test_Result'].apply(
                lambda x: (x == 'PASS').sum() / len(x) * 100
            ).reset_index()
            ts_data.columns = ['Date', 'Yield']
        elif request.metric == 'test_time':
            # Calculate average test time
            ts_data = df.groupby('Date')['Test_Time_sec'].mean().reset_index()
            ts_data.columns = ['Date', 'Test_Time']
        else:
            raise HTTPException(status_code=400, detail="Invalid metric")
        
        # Create forecast
        if request.method == 'prophet':
            forecaster = ProphetForecaster()
            forecast = forecaster.fit_predict(
                ts_data, 
                date_col='Date',
                value_col=ts_data.columns[1],
                periods=request.periods
            )
        elif request.method == 'arima':
            forecaster = ARIMAForecaster()
            forecast = forecaster.fit_predict(
                ts_data[ts_data.columns[1]].values,
                periods=request.periods
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid forecasting method")
        
        return {
            "forecast": forecast.to_dict('records') if isinstance(forecast, pd.DataFrame) else forecast.tolist(),
            "method": request.method,
            "periods": request.periods,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Forecasting error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/insights/generate")
async def generate_insights():
    """Generate AI-powered insights"""
    try:
        df = load_data()
        analyzer = YieldAnalyzer(df)
        overall = analyzer.overall_yield()
        
        # Generate insights
        generator = InsightGenerator()
        yield_insight = generator.generate_yield_insight(
            current_yield=overall['Yield %'],
            target_yield=95.0,
            trend='stable'
        )
        
        # Generate recommendations
        engine = RecommendationEngine()
        recommendations = engine.generate_recommendations({
            'yield': overall['Yield %'],
            'avg_test_time': df['Test_Time_sec'].mean(),
            'anomaly_rate': 0.05
        })
        
        return {
            "insights": [yield_insight],
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Insights generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/insights/rca")
async def root_cause_analysis():
    """Perform root cause analysis on failures"""
    try:
        df = load_data()
        analyzer = RootCauseAnalyzer()
        
        # Analyze failures
        rca_results = analyzer.analyze_failures(df)
        report = analyzer.generate_rca_report(rca_results)
        
        return {
            "analysis": rca_results,
            "report": report,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"RCA error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/model/train")
async def train_model(background_tasks: BackgroundTasks, model_type: str = "random_forest"):
    """Train ML model in background"""
    try:
        def train_task():
            df = load_data()
            model = YieldPredictionModel(model_type=model_type)
            metrics = model.train(df)
            trained_models['yield_model'] = model
            logger.info(f"Model trained. Accuracy: {metrics['test']['accuracy']:.4f}")
        
        background_tasks.add_task(train_task)
        
        return {
            "status": "training_started",
            "model_type": model_type,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Training error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/model/metrics")
async def get_model_metrics():
    """Get trained model metrics"""
    try:
        if 'yield_model' not in trained_models:
            raise HTTPException(status_code=404, detail="No trained model found")
        
        model = trained_models['yield_model']
        
        # Get feature importance
        importance = model.feature_importance()
        
        return {
            "model_type": model.model_type,
            "feature_importance": importance.to_dict('records') if isinstance(importance, pd.DataFrame) else {},
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export/data")
async def export_data(format: str = "csv"):
    """Export data in specified format"""
    try:
        df = load_data()
        
        if format == "csv":
            output = io.StringIO()
            df.to_csv(output, index=False)
            return JSONResponse(content={"data": output.getvalue()})
        elif format == "json":
            return df.to_dict('records')
        else:
            raise HTTPException(status_code=400, detail="Invalid format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "timestamp": datetime.now().isoformat()}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
