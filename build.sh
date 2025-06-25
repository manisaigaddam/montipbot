#!/bin/bash
set -e

# Create a temporary directory for pip cache
mkdir -p /tmp/pip-cache
export PIP_CACHE_DIR=/tmp/pip-cache

# Create a temporary directory for cargo
mkdir -p /tmp/cargo-cache
export CARGO_HOME=/tmp/cargo-cache

# Install Python dependencies with --no-build-isolation to avoid Rust compilation
pip install --upgrade pip

# Install specific versions of problematic packages using binary wheels
pip install --only-binary :all: web3==5.31.3
pip install --only-binary :all: eth-account==0.7.0
pip install --only-binary :all: cryptography==41.0.1

# Install remaining packages from requirements.txt, excluding the ones we already installed
grep -v "web3\|eth-account\|cryptography" requirements.txt > filtered_requirements.txt
pip install -r filtered_requirements.txt

# Clean up
rm filtered_requirements.txt

echo "Build completed successfully!" 
