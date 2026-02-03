#!/usr/bin/env python3
"""
Test script to verify budget change request validations.
"""
import json
import sys
import os
import importlib.util

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import handler using importlib since 'lambda' is a reserved keyword
handler_path = os.path.join(current_dir, 'lambda', 'jobs', 'request_price_change', 'handler.py')
spec = importlib.util.spec_from_file_location("request_price_change_handler", handler_path)
handler_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handler_module)
handler = handler_module.handler


def test_duplicate_pending_request():
    """Test BR-BUD-03: Cannot create second pending request"""
    print('\n' + '=' * 80)
    print('TEST 1: Attempting to create duplicate pending request')
    print('Expected: Should reject with 400 error')
    print('=' * 80)

    test_event = {
        'requestContext': {
            'authorizer': {
                'jwt': {
                    'claims': {
                        'sub': 'cognito-sp-001'
                    }
                }
            }
        },
        'pathParameters': {
            'jobId': '1041'
        },
        'body': json.dumps({
            'proposed_final_price': 400.00,
            'reason': 'Even more work needed than previously estimated'
        })
    }

    result = handler(test_event, None)
    response = json.loads(result['body'])

    print(f'Status Code: {result["statusCode"]}')
    print(f'Message: {response.get("message")}')

    if result['statusCode'] == 400 and 'already exists' in response.get('message', '').lower():
        print('✅ TEST PASSED: Correctly rejected duplicate pending request')
        return True
    else:
        print('❌ TEST FAILED: Should have rejected the request')
        return False


def test_invalid_job_status():
    """Test BR-BUD-02: Can only request when job is in_progress"""
    print('\n' + '=' * 80)
    print('TEST 2: Attempting request on non-in_progress job')
    print('Expected: Should reject with 400 error')
    print('=' * 80)

    # First, create a test job in 'open' status
    from src.db.rds_main import get_connection
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            # Find or create a job in 'open' status assigned to our provider
            cur.execute('''
                SELECT job_id FROM jobs
                WHERE assigned_provider_id = 'SP-001' AND status = 'open'
                LIMIT 1
            ''')
            job = cur.fetchone()

            if not job:
                # Create a temporary job for testing
                cur.execute('''
                    INSERT INTO jobs (customer_id, title, description, location_address, status, assigned_provider_id)
                    VALUES (1, 'Test Job', 'Test Description', 'Test Address', 'open', 'SP-001')
                ''')
                conn.commit()
                job_id = cur.lastrowid
            else:
                job_id = job['job_id']

            print(f'Testing with job_id: {job_id} (status: open)')
    finally:
        conn.close()

    test_event = {
        'requestContext': {
            'authorizer': {
                'jwt': {
                    'claims': {
                        'sub': 'cognito-sp-001'
                    }
                }
            }
        },
        'pathParameters': {
            'jobId': str(job_id)
        },
        'body': json.dumps({
            'proposed_final_price': 300.00,
            'reason': 'This should fail because job is not in_progress'
        })
    }

    result = handler(test_event, None)
    response = json.loads(result['body'])

    print(f'Status Code: {result["statusCode"]}')
    print(f'Message: {response.get("message")}')

    if result['statusCode'] == 400 and 'in_progress' in response.get('message', '').lower():
        print('✅ TEST PASSED: Correctly rejected request on non-in_progress job')
        return True
    else:
        print('❌ TEST FAILED: Should have rejected the request')
        return False


def test_price_validation():
    """Test that proposed price must be >= current final price"""
    print('\n' + '=' * 80)
    print('TEST 3: Attempting request with price lower than current final_price')
    print('Expected: Should reject with 400 error')
    print('=' * 80)

    test_event = {
        'requestContext': {
            'authorizer': {
                'jwt': {
                    'claims': {
                        'sub': 'cognito-sp-001'
                    }
                }
            }
        },
        'pathParameters': {
            'jobId': '1041'  # Current final_price is $250
        },
        'body': json.dumps({
            'proposed_final_price': 200.00,  # Lower than current $250
            'reason': 'This should fail because price is lower than current'
        })
    }

    # First, reject the pending request so we can test this
    from src.db.rds_main import get_connection
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE job_price_change_requests
                SET status = 'rejected', responded_at = NOW()
                WHERE job_id = 1041 AND status = 'pending'
            ''')
            cur.execute('''
                UPDATE jobs
                SET status = 'in_progress'
                WHERE job_id = 1041
            ''')
            conn.commit()
    finally:
        conn.close()

    result = handler(test_event, None)
    response = json.loads(result['body'])

    print(f'Status Code: {result["statusCode"]}')
    print(f'Message: {response.get("message")}')

    if result['statusCode'] == 400 and ('greater than' in response.get('message', '').lower() or 'current' in response.get('message', '').lower()):
        print('✅ TEST PASSED: Correctly rejected price lower than current final_price')
        return True
    else:
        print('❌ TEST FAILED: Should have rejected the request')
        return False


def test_reason_length_validation():
    """Test that reason must be at least 10 characters"""
    print('\n' + '=' * 80)
    print('TEST 4: Attempting request with short reason')
    print('Expected: Should reject with 400 error')
    print('=' * 80)

    test_event = {
        'requestContext': {
            'authorizer': {
                'jwt': {
                    'claims': {
                        'sub': 'cognito-sp-001'
                    }
                }
            }
        },
        'pathParameters': {
            'jobId': '1041'
        },
        'body': json.dumps({
            'proposed_final_price': 300.00,
            'reason': 'Too short'  # Only 9 characters
        })
    }

    result = handler(test_event, None)
    response = json.loads(result['body'])

    print(f'Status Code: {result["statusCode"]}')
    print(f'Message: {response.get("message")}')

    if result['statusCode'] == 400 and '10 characters' in response.get('message', ''):
        print('✅ TEST PASSED: Correctly rejected short reason')
        return True
    else:
        print('❌ TEST FAILED: Should have rejected the request')
        return False


if __name__ == '__main__':
    print('=' * 80)
    print('BUDGET CHANGE REQUEST VALIDATION TESTS')
    print('=' * 80)

    results = []

    # Run tests
    results.append(('Duplicate Pending Request', test_duplicate_pending_request()))
    results.append(('Invalid Job Status', test_invalid_job_status()))
    results.append(('Price Validation', test_price_validation()))
    results.append(('Reason Length Validation', test_reason_length_validation()))

    # Print summary
    print('\n' + '=' * 80)
    print('TEST SUMMARY')
    print('=' * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = '✅ PASSED' if result else '❌ FAILED'
        print(f'{status}: {test_name}')

    print('\n' + '=' * 80)
    if passed == total:
        print(f'🎉 ALL TESTS PASSED ({passed}/{total})')
    else:
        print(f'⚠️  SOME TESTS FAILED ({passed}/{total} passed)')
    print('=' * 80)
