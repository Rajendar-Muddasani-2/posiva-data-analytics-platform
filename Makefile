# Makefile for POSIVA Analytics Platform
# Quick commands for common tasks

.PHONY: help setup install test lint format clean run-dashboard run-notebook

help:
	@echo "POSIVA Analytics Platform - Make Commands"
	@echo "=========================================="
	@echo "setup          - Set up project environment"
	@echo "install        - Install dependencies"
	@echo "test           - Run tests"
	@echo "test-cov       - Run tests with coverage"
	@echo "lint           - Lint code"
	@echo "format         - Format code with black"
	@echo "clean          - Clean cache and temp files"
	@echo "run-dashboard  - Start Streamlit dashboard"
	@echo "run-notebook   - Start Jupyter Lab"
	@echo "docker-build   - Build Docker image"
	@echo "docker-run     - Run Docker container"

setup:
	@echo "Setting up environment..."
	python scripts/setup_environment.py

install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt

install-dev:
	@echo "Installing dev dependencies..."
	pip install -r requirements.txt
	pip install pytest pytest-cov black flake8 mypy

test:
	@echo "Running tests..."
	pytest tests/ -v

test-cov:
	@echo "Running tests with coverage..."
	pytest tests/ --cov=src --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/index.html"

lint:
	@echo "Linting code..."
	flake8 src/ tests/ --max-line-length=100
	mypy src/

format:
	@echo "Formatting code..."
	black src/ tests/ notebooks/ webapp/
	isort src/ tests/ notebooks/ webapp/

clean:
	@echo "Cleaning cache and temp files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	@echo "Cleaned!"

run-dashboard:
	@echo "Starting Streamlit dashboard..."
	streamlit run webapp/app.py

run-notebook:
	@echo "Starting Jupyter Lab..."
	jupyter lab

docker-build:
	@echo "Building Docker image..."
	docker build -t posiva-analytics:latest .

docker-run:
	@echo "Running Docker container..."
	docker run -p 8501:8501 -v $(PWD)/data:/app/data posiva-analytics:latest

# Development helpers
watch-tests:
	@echo "Running tests in watch mode..."
	pytest-watch tests/

generate-docs:
	@echo "Generating documentation..."
	cd docs && make html

# Quick data processing
process-data:
	@echo "Processing data..."
	python src/pipeline/etl_pipeline.py

generate-report:
	@echo "Generating report..."
	python src/reporting/report_generator.py
