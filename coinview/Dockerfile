# coinview/Dockerfile

# Use the official Python image as base
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install build tools and dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    cmake \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Download and extract TA-Lib source code
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && \
    ./configure -prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Copy Python requirements
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire coinview directory into the container
COPY . /app

# Command to run the Flask app
CMD ["python", "app.py"]
