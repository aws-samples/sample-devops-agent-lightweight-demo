#!/bin/bash
set -e

echo "========================================="
echo "AWS DevOps Agent Demo - CDK Setup"
echo "========================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment
echo ""
echo "Creating Python virtual environment..."
python3 -m venv .venv

# Activate and install dependencies
echo "Installing CDK dependencies..."
.venv/bin/pip install --upgrade pip > /dev/null
.venv/bin/pip install -r requirements.txt

echo ""
echo "========================================="
echo "✅ CDK setup complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Activate venv: source .venv/bin/activate"
echo "2. Bootstrap CDK (first time): cdk bootstrap"
echo "3. Deploy: cdk deploy"
echo ""
