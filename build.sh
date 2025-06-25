#!/bin/bash
set -e

echo "Starting build process..."

# Install Rust locally (to writable directory)
export CARGO_HOME=$HOME/.cargo
export RUSTUP_HOME=$HOME/.rustup
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

echo "Build completed successfully!" 
