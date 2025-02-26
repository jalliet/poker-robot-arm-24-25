#!/bin/bash

# Create and activate virtual environment
# Make sure to use a Python version under 3.13
python -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r ../requirements.txt

echo "Installation complete! To activate the virtual environment, run:"
echo "source venv/bin/activate."
