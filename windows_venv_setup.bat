@echo off

REM Create and activate virtual environment
REM Make sure to use a Python version under 3.13
python3.12 -m venv venv

REM Activate the virtual environment
call venv\Scripts\activate

REM Upgrade pip
pip install --upgrade pip

REM Install requirements
pip install -r requirements.txt

echo Installation complete! To activate the virtual environment, run:
echo call venv\Scripts\activate.bat

