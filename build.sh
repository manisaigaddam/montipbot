#!/bin/bash
set -e

echo "Starting build process..."

# Upgrade pip and install wheel
pip install --upgrade pip wheel setuptools

# Install dependencies with binary packages only
pip install --only-binary=:all: -r requirements.txt || pip install -r requirements.txt

echo "Build completed successfully!" 