import json
from typing import Any, Dict, Iterable, List


def extract_jwt_claims(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract JWT claims from common API Gateway authorizer shapes.
    Supports HTTP API v2 JWT authorizer and REST API custom authorizer payloads.
    """
    request_context = event.get("requestContext", {}) or {}
    authorizer = request_context.get("authorizer", {}) or {}

    jwt_claims = (authorizer.get("jwt") or {}).get("claims") or {}
    if isinstance(jwt_claims, dict) and jwt_claims:
        return jwt_claims

    legacy_claims = authorizer.get("claims") or {}
    if isinstance(legacy_claims, dict) and legacy_claims:
        return legacy_claims

    return {}


def _normalize_groups(raw_groups: Any) -> List[str]:
    """
    Normalize group claims to a list of strings.
    Cognito typically provides `cognito:groups` as a list, but some custom
    authorizers may pass a comma-separated string or serialized JSON array.
    """
    if not raw_groups:
        return []

    if isinstance(raw_groups, list):
        return [str(group).strip() for group in raw_groups if str(group).strip()]

    if isinstance(raw_groups, str):
        text = raw_groups.strip()
        if not text:
            return []

        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    return [str(group).strip() for group in parsed if str(group).strip()]
            except json.JSONDecodeError:
                pass

        if "," in text:
            return [segment.strip() for segment in text.split(",") if segment.strip()]

        return [text]

    return [str(raw_groups).strip()]


def has_cognito_group(
    claims: Dict[str, Any],
    required_groups: Iterable[str],
    group_claim_key: str = "cognito:groups",
) -> bool:
    """Return True when the claims include any required group."""
    groups = set(_normalize_groups(claims.get(group_claim_key)))
    required = {group.strip() for group in required_groups if str(group).strip()}
    return bool(groups.intersection(required))


def is_cognito_administrator(
    claims: Dict[str, Any],
    group_claim_key: str = "cognito:groups",
) -> bool:
    """
    Validate administrator group membership.
    Includes both `Administrator` and `Adminstrator` to support existing typoed group names.
    """
    return has_cognito_group(
        claims,
        required_groups=("Administrator", "Adminstrator"),
        group_claim_key=group_claim_key,
    )
