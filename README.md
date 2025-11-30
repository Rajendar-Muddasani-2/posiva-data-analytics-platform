# POSIVA Advanced Analytics Platform 🚀

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/kubernetes-%23326ce5.svg?logo=kubernetes&logoColor=white)](https://kubernetes.io/)

**Enterprise-grade, production-ready data analytics and machine learning platform for semiconductor manufacturing.**

Transform raw ATE data into actionable insights through advanced analytics, statistical rigor, AI-powered intelligence, and deep learning. **Fully deployed with CI/CD, Docker, Kubernetes, and comprehensive monitoring.**

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Documentation](#documentation)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

POSIVA is a **production-ready** comprehensive analytics platform designed for semiconductor validation and manufacturing engineers. It automates data ingestion, performs advanced statistical analysis, builds predictive ML/DL models, generates AI-powered insights, and provides REST API access—all while teaching you industry-standard data science practices aligned with the Google Data Analytics Advanced Certificate.

**Key Capabilities:**
- 🔄 Automated ETL pipelines for STDF and V93K data
- 📊 Advanced analytics (yield, test time, bins, wafer maps, parametric)
- 📈 Statistical analysis (hypothesis testing, A/B tests, time series forecasting)
- 🤖 Machine learning (prediction, classification, clustering, deep learning)
- 🧠 AI-powered insights (NLG, root cause analysis, model explainability)
- 📱 Interactive dashboards (Streamlit with 5 specialized pages)
- 🔌 REST API (FastAPI with 15+ endpoints)
- 🐳 Production deployment (Docker, Kubernetes, CI/CD)
- 📊 Comprehensive monitoring (Prometheus + Grafana)
- 📄 Automated reporting (PDF, HTML, Email)

---

## ✨ Features

### Data Engineering
- ✅ Multi-format ingestion (STDF, V93K logs, CSV)
- ✅ Data quality framework with automated validation
- ✅ Data profiling and cleaning
- ✅ Parquet-based data lake architecture
- ✅ PostgreSQL for structured data
- ✅ Redis for caching

### Analytics Suite
- ✅ **Yield Analytics:** Trends, Pareto, control charts, device/test/lot/wafer analysis
- ✅ **Test Time Optimization:** Hotspot identification, bottleneck detection, optimization recommendations
- ✅ **Bin Analysis:** Distribution, migration, co-occurrence patterns
- ✅ **Wafer Intelligence:** Spatial statistics, pattern recognition, cluster analysis
- ✅ **Parametric Analysis:** Cpk analysis, distribution fitting, outlier detection, correlation analysis

### Statistical Methods
- ✅ Hypothesis testing (t-tests, chi-square, ANOVA, Mann-Whitney U, Kruskal-Wallis)
- ✅ A/B testing framework with sample size calculations
- ✅ Time series forecasting (ARIMA/SARIMA, Prophet, Exponential Smoothing)
- ✅ Forecast comparison framework
- ✅ Normality tests (Shapiro-Wilk, Kolmogorov-Smirnov)
- ✅ Confidence intervals

### Machine Learning
- ✅ Supervised learning (Random Forest, XGBoost, Logistic Regression, Gradient Boosting)
- ✅ Unsupervised learning (K-Means, DBSCAN, Isolation Forest)
- ✅ Model evaluation with cross-validation
- ✅ Feature importance analysis
- ✅ Hyperparameter tuning

### Deep Learning (NEW!)
- ✅ **Neural Networks:** 3-layer feedforward with batch normalization & dropout
- ✅ **LSTM:** Recurrent networks for time series forecasting
- ✅ **Autoencoders:** Unsupervised anomaly detection via reconstruction error
- ✅ TensorFlow/Keras integration
- ✅ Early stopping & learning rate scheduling
- ✅ Model persistence & loading

### AI-Powered Insights (NEW!)
- ✅ **Natural Language Generation:** Automated insight generation in human-readable format
- ✅ **Root Cause Analysis:** Automated failure analysis with ranked causes and severity
- ✅ **Model Explainability:** SHAP & LIME integration for feature importance
- ✅ **Recommendation Engine:** Rule-based intelligent recommendations
- ✅ Severity ranking (HIGH/MEDIUM/LOW)
- ✅ Confidence scoring

### Visualization & Dashboards
- ✅ Interactive Plotly visualizations
- ✅ **5-page Streamlit dashboard:**
  1. Home (overview, quick stats)
  2. Yield Analytics (device/test/lot/wafer yield)
  3. Test Time Analytics (performance optimization)
  4. Parametric Analytics (Cpk, distributions, outliers, correlations)
  5. ML Predictions (model training, predictions, anomaly detection)
- ✅ 30+ chart types
- ✅ Drill-down and filtering
- ✅ Real-time updates

### REST API (NEW!)
- ✅ **FastAPI** with 15+ endpoints
- ✅ Endpoints: `/api/health`, `/api/analytics/yield`, `/api/predict/yield`, `/api/forecast`, `/api/insights/generate`, `/api/insights/rca`
- ✅ Request/response validation with Pydantic
- ✅ CORS middleware
- ✅ Background task processing
- ✅ Batch predictions via CSV upload
- ✅ Comprehensive error handling
- ✅ Auto-generated OpenAPI docs (Swagger)

### Production Deployment (NEW!)
- ✅ **CI/CD Pipeline:** GitHub Actions with automated testing, linting, Docker build
- ✅ **Docker Compose:** Production stack (dashboard, API, PostgreSQL, Redis, Prometheus, Grafana, MLflow, Nginx)
- ✅ **Kubernetes:** Deployment with HPA (2-10 replicas), persistent volumes, health checks
- ✅ **Monitoring:** Prometheus metrics + Grafana dashboards
- ✅ **Cloud Ready:** AWS (ECS/EKS), GCP (Cloud Run/GKE), Azure (ACI/AKS)
- ✅ **Load Balancing:** Nginx reverse proxy
- ✅ **SSL/TLS:** Certificate management

### Automation
- ✅ Automated daily/weekly/monthly reports
- ✅ Email and Slack notifications
- ✅ MLflow experiment tracking
- ✅ Model versioning
- ✅ Automated retraining triggers

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- Docker & Docker Compose (for production)
- 8GB+ RAM
- 10GB+ disk space
- macOS, Linux, or Windows

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd posiva_data_analytics
```

2. **Quick Setup Script**
```bash
chmod +x quickstart.sh
./quickstart.sh
```
This will:
- Create virtual environment
- Install dependencies
- Generate sample data
- Run demo
- Display next steps

### Manual Installation (Alternative)

1. **Create virtual environment**
```bash
# Using venv
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# OR using conda
conda env create -f environment.yml
conda activate posiva
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your settings (optional for local dev)
```

3. **Generate sample data**
```bash
python src/utils/data_generator.py
```

4. **Run quick demo**
```bash
python demo.py
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your settings
```

4. **Verify installation**
```bash
python scripts/setup_environment.py
```

### Run Your First Analysis

```bash
# Start Jupyter Lab
jupyter lab

# Open: notebooks/00_setup_and_environment.ipynb
```

### Launch Dashboard

```bash
streamlit run webapp/app.py
```

Visit: http://localhost:8501

---

## 📁 Project Structure

```
posiva_data_analytics/
├── data/                  # Data directory (gitignored)
│   ├── raw/              # Raw ingested data
│   ├── processed/        # Cleaned data
│   ├── features/         # ML features
│   └── sample/           # Sample data (committed)
├── notebooks/            # Jupyter notebooks (19 notebooks)
├── src/                  # Source code (Python package)
│   ├── ingestion/        # Data parsers
│   ├── quality/          # Data quality
│   ├── analytics/        # Analytics modules
│   ├── statistical/      # Statistical methods
│   ├── ml/               # Machine learning
│   ├── dl/               # Deep learning
│   ├── ai/               # AI/NLG
│   ├── visualization/    # Plotting utilities
│   ├── reporting/        # Report generation
│   ├── utils/            # Utilities
│   └── pipeline/         # Orchestration
├── webapp/               # Streamlit dashboard
├── tests/                # Unit and integration tests
├── models/               # Saved ML models
├── reports/              # Generated reports
├── docs/                 # Documentation
├── scripts/              # Utility scripts
└── requirements.txt      # Python dependencies
```

---

## 📚 Documentation

- **[PRD.md](PRD.md)** - Complete product requirements document
- **[User Guide](docs/user_guide.md)** - How to use the platform
- **[API Reference](docs/api_reference.md)** - Code documentation
- **[Deployment Guide](docs/deployment.md)** - Production deployment

---

## 💻 Development

### Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/test_analytics.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
flake8 src/ tests/

# Type check
mypy src/
```

### Development Workflow

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and test locally
3. Run tests: `pytest`
4. Format code: `black .`
5. Commit: `git commit -m "Add feature"`
6. Push: `git push origin feature/your-feature`
7. Create Pull Request

---

## 📊 Usage Examples

### Data Ingestion
```python
from src.ingestion import STDFParser

parser = STDFParser()
df = parser.parse("data/raw/stdf/lot123.stdf")
df.to_parquet("data/processed/lot123.parquet")
```

### Yield Analytics
```python
from src.analytics import YieldAnalytics

ya = YieldAnalytics(df)
yield_by_lot = ya.calculate_yield_by_lot()
ya.plot_yield_trend()
```

### Machine Learning
```python
from src.ml.models import YieldPredictor

model = YieldPredictor()
model.train(X_train, y_train)
predictions = model.predict(X_test)
model.save("models/yield_predictor.pkl")
```

---

## 🎓 Learning Path

This project is aligned with the **Google Data Analytics Advanced Certificate**. Work through notebooks sequentially:

**Weeks 1-2:** Notebooks 00-02 (Setup, Ingestion, Cleaning)  
**Weeks 3-5:** Notebooks 03-08 (EDA, Core Analytics)  
**Weeks 6-8:** Notebooks 09-14 (Statistics, ML)  
**Weeks 9-12:** Notebooks 15-19 (Advanced Topics)  
**Weeks 13-16:** Dashboard, Automation, Deployment  

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Ensure all tests pass
5. Submit a pull request

See [CONTRIBUTING.md](docs/contributing.md) for details.

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

---

## 🙏 Acknowledgments

- Google Data Analytics Professional Certificate curriculum
- Open-source data science community
- Semiconductor validation engineering teams

---

## 📞 Contact

**Project Owner:** Rajendar Muddasani  
**Issues:** [GitHub Issues](https://github.com/your-repo/issues)  
**Discussions:** [GitHub Discussions](https://github.com/your-repo/discussions)

---

## ⭐ Star History

If you find this project useful, please consider giving it a star! ⭐

---

**Built with ❤️ for data-driven semiconductor validation**
