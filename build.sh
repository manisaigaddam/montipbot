#!/bin/bash
set -e

echo "Starting custom build process..."

# Create a clean virtual environment
python -m venv /tmp/venv
source /tmp/venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install packages one by one with specific versions known to have binary wheels
echo "Installing dependencies..."
pip install fastapi==0.95.2
pip install "uvicorn[standard]==0.22.0"
pip install python-dotenv==1.0.0
pip install httpx==0.24.1
pip install requests==2.31.0
pip install pydantic==1.10.8
pip install gunicorn==21.2.0

# Install web3 and related packages with versions known to work without Rust
echo "Installing web3 ecosystem..."
pip install eth-abi==2.2.0
pip install eth-account==0.7.0
pip install eth-hash==0.5.1
pip install eth-typing==3.3.0
pip install eth-utils==2.1.0
pip install hexbytes==0.3.0
pip install web3==5.31.3

# Install cryptography with a version known to have binary wheels
echo "Installing cryptography..."
pip install cryptography==38.0.4

# Install supabase client
echo "Installing supabase client..."
pip install supabase==1.0.3

# Copy all installed packages to the main Python environment
pip freeze > /tmp/requirements-lock.txt
pip install -r /tmp/requirements-lock.txt

echo "Build completed successfully!" 
