# Create and activate virtual environment
# Make sure to use a Python version under 3.13
python3.12 -m venv venv

# Activate the virtual environment
.\venv\Scripts\Activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

Write-Host "Installation complete! To activate the virtual environment, run:"
Write-Host ".\venv\Scripts\Activate.ps1"
