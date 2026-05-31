FROM python:3.11-slim

# Set Python environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MODEL_PATH=/app/models/final_model.joblib \
    METADATA_PATH=/app/models/final_model_metadata.json

WORKDIR /app

# Install system utilities and build dependencies (needed for compiling certain wheels if necessary)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies first to cache this layer
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY app/ /app/app/
COPY models/ /app/models/
COPY data/ /app/data/

# Expose FastAPI and Streamlit standard ports
EXPOSE 8000
EXPOSE 8501

# Default command launches the API. In docker-compose, this will be run separately for api and ui.
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
