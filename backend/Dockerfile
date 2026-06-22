# Use a lightweight official Python runtime as a parent image
FROM python:3.10-slim

# Set system environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV RUNNING_IN_DOCKER=true
# 🔴 FIX: Explicitly inject workspace to Python path so absolute imports work natively
ENV PYTHONPATH=/workspace

# Set the working directory to the project root
WORKDIR /workspace

# Install system dependencies required for potential image processing libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from the correct relative path inside backend/
COPY backend/requirements.txt /workspace/requirements.txt
RUN pip install --no-cache-dir -r /workspace/requirements.txt

# 🔴 FIX: Copy everything to the root so the backend folder retains its top-level packaging
COPY . /workspace/

# Expose the production port for FastAPI
EXPOSE 8000

# Run Uvicorn pointing directly to the application layer module
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]