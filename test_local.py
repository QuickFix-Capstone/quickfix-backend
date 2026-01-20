"""
Local Flask wrapper for testing Lambda functions with Postman
Run this file and use Postman to test endpoints locally
"""
from flask import Flask, request, jsonify
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Lambda handler
from lambda.Service_Provider.create_job_application.handler import handler

app = Flask(__name__)


@app.route('/jobs/<job_id>/applications', methods=['POST', 'OPTIONS'])
def create_job_application(job_id):
    """
    Test endpoint for create_job_application Lambda function
    
    POST /jobs/{job_id}/applications
    Headers:
        Authorization: Bearer <token> (optional for local testing)
    Body:
        {
            "proposed_price": 150.00,
            "message": "I'm interested in this job"
        }
    """
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 200
    
    # Get Authorization header (for testing, we'll extract a mock cognito_sub)
    auth_header = request.headers.get('Authorization', '')
    
    # For local testing, you can hardcode a cognito_sub or extract from header
    # Format: "Bearer <cognito_sub>" or just use a test value
    if auth_header.startswith('Bearer '):
        cognito_sub = auth_header.replace('Bearer ', '')
    else:
        # Default test cognito_sub - CHANGE THIS to match a real provider in your DB
        cognito_sub = "test-cognito-sub-123"
    
    # Build Lambda event object
    event = {
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": cognito_sub
                    }
                }
            }
        },
        "pathParameters": {
            "job_id": job_id
        },
        "body": request.get_data(as_text=True)
    }
    
    # Call the Lambda handler
    response = handler(event, None)
    
    # Return the response
    return (
        response.get('body', '{}'),
        response.get('statusCode', 500),
        {'Content-Type': 'application/json'}
    )


@app.after_request
def after_request(response):
    """Add CORS headers to all responses"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    return response


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 QuickFix Backend - Local Testing Server")
    print("="*60)
    print("\n📍 Endpoint: POST http://localhost:5000/jobs/{job_id}/applications")
    print("\n📝 Example Request:")
    print("   URL: http://localhost:5000/jobs/1/applications")
    print("   Method: POST")
    print("   Headers:")
    print("     Content-Type: application/json")
    print("     Authorization: Bearer <your-cognito-sub>")
    print("   Body:")
    print("     {")
    print('       "proposed_price": 150.00,')
    print('       "message": "I am interested in this job"')
    print("     }")
    print("\n" + "="*60 + "\n")
    
    app.run(debug=True, port=5000)
