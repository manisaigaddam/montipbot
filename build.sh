#!/bin/bash
set -e

echo "Starting custom build process..."

# Create clean requirements file with versions known to have binary wheels
cat > requirements-simple.txt << EOF
fastapi==0.95.2
uvicorn[standard]==0.22.0
web3==5.31.3
python-dotenv==1.0.0
httpx==0.24.1
eth-account==0.7.0
requests==2.31.0
pydantic==1.10.8
supabase==1.0.3
cryptography==38.0.4
gunicorn==21.2.0
EOF

# Upgrade pip
pip install --upgrade pip

# Try to install everything using binary wheels only
echo "Installing dependencies with binary wheels only..."
pip install --only-binary=:all: -r requirements-simple.txt || {
  echo "Failed to install all packages with binary wheels only, falling back to individual installs..."
  
  # Install packages one by one with specific versions known to have binary wheels
  pip install fastapi==0.95.2
  pip install "uvicorn[standard]==0.22.0"
  pip install python-dotenv==1.0.0
  pip install httpx==0.24.1
  pip install requests==2.31.0
  pip install pydantic==1.10.8
  pip install gunicorn==21.2.0
  
  # Install web3 and related packages with versions known to work without Rust
  pip install eth-abi==2.2.0
  pip install eth-account==0.7.0
  pip install eth-hash==0.5.1
  pip install eth-typing==3.3.0
  pip install eth-utils==2.1.0
  pip install hexbytes==0.3.0
  pip install web3==5.31.3
  
  # Install cryptography with a version known to have binary wheels
  pip install cryptography==38.0.4
  
  # Install supabase client
  pip install supabase==1.0.3
}

echo "Build completed successfully!" 
