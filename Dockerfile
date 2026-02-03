# Multi-Platform Build for RVM Edge
# Target: linux/arm64 (Raspberry Pi / Jetson Orin)
FROM python:3.10-slim

# Prevent interactive prompts during apt install
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies for OpenCV, Git, and networking
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    git \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# NOTE: Edge application interacts with host systemctl and hardware.
# When running in Docker, ensure appropriate device mapping and 
# host socket access if systemctl control is needed.
# For production edge deployment, Rule 63 recommends Native Python.

CMD ["python", "main.py"]
