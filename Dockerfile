# Use Python 3.12 slim base image
FROM python:3.12-slim

# Environment setup
ENV POETRY_VERSION=1.8.2
ENV PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONPATH=/app/src

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install "poetry==$POETRY_VERSION"

# Set working directory
WORKDIR /app

# Copy only dependency files first for caching
COPY pyproject.toml poetry.lock* ./

# Install dependencies (no project code yet for caching)
RUN poetry install --no-root

# Copy full project including src/
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Start the FastAPI app via Uvicorn (with module path from src)
CMD ["uvicorn", "planet.application:app", "--host", "0.0.0.0", "--port", "8000"]
