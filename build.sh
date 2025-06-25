#!/bin/bash
set -e

# Install Rust and required build tools
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"

# Install system dependencies
apt-get update || true
apt-get install -y build-essential || true

# Install Python dependencies with proper environment for Rust compilation
export CARGO_NET_GIT_FETCH_WITH_CLI=true
export RUSTFLAGS="-C target-feature=-crt-static"
pip install --upgrade pip
pip install -r requirements.txt

echo "Build completed successfully!" 