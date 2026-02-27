import os
import sys


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


from src.utils.auth import (
    extract_jwt_claims,
    has_cognito_group,
    is_cognito_administrator,
)


def test_extract_jwt_claims_http_api_v2_shape():
    event = {
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": "abc-123",
                        "cognito:groups": ["Administrator"],
                    }
                }
            }
        }
    }
    claims = extract_jwt_claims(event)
    assert claims["sub"] == "abc-123"


def test_extract_jwt_claims_legacy_shape():
    event = {
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": "legacy-1",
                    "cognito:groups": "Administrator",
                }
            }
        }
    }
    claims = extract_jwt_claims(event)
    assert claims["sub"] == "legacy-1"


def test_has_cognito_group_with_csv_string():
    claims = {"cognito:groups": "Customer,Administrator"}
    assert has_cognito_group(claims, ["Administrator"]) is True


def test_is_cognito_administrator_supports_typo_group_name():
    claims = {"cognito:groups": ["Adminstrator"]}
    assert is_cognito_administrator(claims) is True
