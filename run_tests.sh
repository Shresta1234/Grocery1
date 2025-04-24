#!/bin/bash

# Activate virtual environment (if using one)
# source .venv/bin/activate

# Install test dependencies
pip install -r requirements.txt

# Run tests with coverage
coverage run -m pytest tests/ -v

# Generate coverage report
coverage report
coverage html

echo "Tests completed. View detailed coverage report in htmlcov/index.html" 