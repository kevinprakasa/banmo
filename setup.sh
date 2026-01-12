#!/bin/bash

# Exit on error
set -e

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3 and try again."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install the package in development mode
echo "Installing package in development mode..."
pip install -e .

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp env.example .env
    echo "Please update the .env file with your credentials."
fi

echo "Setup complete! You can now run 'stockbit-analyzer' to start the application."
echo "Remember to source venv/bin/activate to activate the virtual environment." 