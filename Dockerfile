# Dockerfile for POSIVA Analytics Platform

FROM python:3.10-slim

LABEL maintainer="Rajendar Muddasani"
LABEL description="POSIVA Analytics Platform - Semiconductor Validation Analytics"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/raw data/processed data/features models reports logs

# Expose port for Streamlit
EXPOSE 8501

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501

# Default command (can be overridden)
CMD ["streamlit", "run", "webapp/app.py"]
