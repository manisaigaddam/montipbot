#!/bin/bash
set -e

echo "Starting build process..."

# Install Rust locally (to writable directory)
export CARGO_HOME=$HOME/.cargo
export RUSTUP_HOME=$HOME/.rustup
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env

# Enable PyO3 forward compatibility for newer Python versions
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies with specific versions for pydantic
pip install pydantic==1.10.8
pip install pydantic-core==2.6.3

# Install remaining dependencies
grep -v "pydantic" requirements.txt > requirements_filtered.txt
pip install -r requirements_filtered.txt

echo "Build completed successfully!" 
