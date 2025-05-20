# Use official Python image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /code

# Install OS dependencies (if any, e.g., for MySQL client)
RUN apt-get update && apt-get install -y gcc build-essential libpq-dev \
    && apt-get install -y default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirement files and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app

# Expose port 8000 for Uvicorn
EXPOSE 8000

# Default command to run when container starts (Uvicorn server)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
