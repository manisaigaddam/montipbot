# Use Python 3.9 slim as the base image (matches Render’s default)
FROM python:3.9-slim

# Install system dependencies for Rust and cryptography
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Set working directory
WORKDIR /app

# Copy project files
COPY requirements.txt .
COPY tip.py .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (Render assigns $PORT dynamically)
EXPOSE $PORT

# Start the application with Gunicorn
CMD ["uvicorn", "tip:app", "--host", "0.0.0.0", "--port", "$PORT"]
