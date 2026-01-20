def get_cognito_sub(event):
    """
    Extracts Cognito user sub from API Gateway HTTP API (v2) event.
    Returns None if not present.
    """
    try:
        return (
            event
            .get("requestContext", {})
            .get("authorizer", {})
            .get("jwt", {})
            .get("claims", {})
            .get("sub")
        )
    except AttributeError:
        return None
