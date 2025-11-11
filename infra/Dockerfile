FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY bridgemind/ ./bridgemind/
COPY data_samples/ ./data_samples/

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "bridgemind.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

