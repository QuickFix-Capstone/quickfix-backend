#!/usr/bin/env bash
# Convenient wrapper to get fresh Service Provider ID token
# Usage: ./get_provider_token.sh [--refresh]

cd "$(dirname "$0")"

# Activate virtual environment and run the Python script
source venv/bin/activate
python3 scripts/get_provider_idtoken.py "$@"
