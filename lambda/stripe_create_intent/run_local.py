#!/usr/bin/env python3
"""
Local runner for stripe_create_intent Lambda function.
Reads Lambda event from stdin, executes handler, writes response to stdout.
"""
import sys
import json
import os
from pathlib import Path

# Load environment variables from .env file
env_file = Path(__file__).parent.parent.parent / '.env'
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)

# Import the Lambda handler
from lambda_function import handler

def main():
    try:
        # Read event from stdin
        event_json = sys.stdin.read()
        event = json.loads(event_json) if event_json else {}
        
        # Execute Lambda handler
        response = handler(event, None)
        
        # Write response to stdout
        print(json.dumps(response, default=str))
        sys.exit(0)
        
    except Exception as e:
        # Return error response in Lambda format
        error_response = {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "error": "Lambda execution error",
                "details": str(e)
            })
        }
        print(json.dumps(error_response))
        sys.exit(1)

if __name__ == '__main__':
    main()
