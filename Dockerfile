# Use official Python slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies and Wasmtime runtime
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    wget \
    libssl-dev \
    libffi-dev \
    libc6 \
    libgcc-s1 \
    libstdc++6 \
    ca-certificates \
    && wget https://github.com/bytecodealliance/wasmtime/releases/download/v21.0.1/wasmtime-v21.0.1-x86_64-linux.tar.xz \
    && tar -xf wasmtime-v21.0.1-x86_64-linux.tar.xz \
    && mv wasmtime-v21.0.1-x86_64-linux/wasmtime /usr/local/bin/wasmtime \
    && chmod +x /usr/local/bin/wasmtime \
    && rm -rf wasmtime-v21.0.1-x86_64-linux* \
    && rm -rf /var/lib/apt/lists/*

# Verify Wasmtime installation
# RUN wasmtime --version

RUN pip install -U didkit

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

EXPOSE 8000

# Run Django server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
