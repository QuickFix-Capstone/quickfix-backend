#!/usr/bin/env bash
# Script to get customer JWT token

cd "$(dirname "$0")"

# Activate virtual environment and run the Python script
source venv/bin/activate
python3 scripts/get_customer_idtoken.py "$@"
