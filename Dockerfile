
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libhdf5-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY Disease-Prediction/requirements.txt /app/requirements.txt

# Remove tensorflow-intel if present (Windows specific) and install requirements
RUN grep -v "tensorflow-intel" requirements.txt > requirements.docker.txt; \
    pip install --no-cache-dir -r requirements.docker.txt

# Copy project
COPY Disease-Prediction/ /app/

# Expose port
EXPOSE 8000

# Run server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
