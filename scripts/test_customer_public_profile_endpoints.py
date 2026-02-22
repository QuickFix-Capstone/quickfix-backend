#!/usr/bin/env python3
"""
End-to-end API test for customer public profile endpoints.

Scenarios:
1) Restricted + no interaction -> 403
2) Restricted + interaction -> 200
3) Invalid sort -> 400

The script discovers a customer that is restricted and currently has no
interaction with the target provider, then inserts a temporary interaction
for the allow-path test, and cleans up afterward.
"""

import argparse
import json
import ssl
import sys
from pathlib import Path
from typing import Optional, Tuple
from urllib.error import HTTPError
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.db.rds_main import get_connection


DEFAULT_API_BASE = "https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod"
DEFAULT_PROVIDER_ID = "SP-905e16ba-6a34-4423-9b23-e8dd31a4b70d"


def api_get(url: str, token: str) -> Tuple[int, dict]:
    req = Request(url=url, method="GET")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")

    try:
        with urlopen(req, context=ssl.create_default_context()) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body or "{}")
    except HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            parsed = json.loads(body or "{}")
        except json.JSONDecodeError:
            parsed = {"raw_body": body}
        return e.code, parsed


def get_provider_sub(provider_id: str) -> Optional[str]:
    conn = get_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT cognito_sub FROM service_providers WHERE provider_id = %s LIMIT 1",
                (provider_id,),
            )
            row = cur.fetchone()
            return row["cognito_sub"] if row else None
    finally:
        conn.close()


def pick_restricted_customer_without_interaction(provider_id: str) -> Optional[int]:
    conn = get_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.customer_id
                FROM customers c
                WHERE c.profile_visibility = 'restricted'
                  AND NOT EXISTS (
                    SELECT 1
                    FROM provider_customer_interactions i
                    WHERE i.provider_id = %s
                      AND i.customer_id = c.customer_id
                  )
                ORDER BY c.customer_id DESC
                LIMIT 1
                """,
                (provider_id,),
            )
            row = cur.fetchone()
            return int(row["customer_id"]) if row else None
    finally:
        conn.close()


def insert_temp_interaction(provider_id: str, customer_id: int, job_id: int) -> None:
    conn = get_connection()
    if not conn:
        raise RuntimeError("DB connection failed")
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO provider_customer_interactions
                    (provider_id, customer_id, interaction_type, job_id, booking_id)
                VALUES (%s, %s, 'message', %s, NULL)
                ON DUPLICATE KEY UPDATE created_at = CURRENT_TIMESTAMP
                """,
                (provider_id, customer_id, job_id),
            )
        conn.commit()
    finally:
        conn.close()


def cleanup_temp_interaction(provider_id: str, customer_id: int, job_id: int) -> None:
    conn = get_connection()
    if not conn:
        return
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM provider_customer_interactions
                WHERE provider_id = %s
                  AND customer_id = %s
                  AND interaction_type = 'message'
                  AND job_id = %s
                  AND booking_id IS NULL
                """,
                (provider_id, customer_id, job_id),
            )
        conn.commit()
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Test customer public profile endpoints")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--provider-id", default=DEFAULT_PROVIDER_ID)
    parser.add_argument("--provider-token", default=None)
    parser.add_argument("--provider-token-file", default="/tmp/jwt_token.txt")
    parser.add_argument("--temp-job-id", type=int, default=999999)
    args = parser.parse_args()

    token = args.provider_token
    if not token:
        token_path = Path(args.provider_token_file)
        if not token_path.exists():
            print("ERROR: provider token not provided and token file not found")
            return 1
        token = token_path.read_text().strip()

    provider_sub = get_provider_sub(args.provider_id)
    if not provider_sub:
        print(f"ERROR: provider {args.provider_id} not found or has no cognito_sub")
        return 1

    customer_id = pick_restricted_customer_without_interaction(args.provider_id)
    if not customer_id:
        print("ERROR: no restricted customer without interaction found")
        return 1

    profile_url = f"{args.api_base}/provider/customers/{customer_id}/profile"
    reviews_url = f"{args.api_base}/provider/customers/{customer_id}/reviews?limit=5&sort=recent"
    invalid_sort_url = f"{args.api_base}/provider/customers/{customer_id}/reviews?sort=invalid_sort"

    print(f"Provider: {args.provider_id}")
    print(f"Customer under test: {customer_id}")

    # 1) No interaction -> 403
    status, body = api_get(profile_url, token)
    ok1 = status == 403
    print(f"[1] profile no interaction: status={status} ok={ok1} body={body}")

    status, body = api_get(reviews_url, token)
    ok2 = status == 403
    print(f"[2] reviews no interaction: status={status} ok={ok2} body={body}")

    inserted = False
    try:
        # 2) Add temporary interaction -> 200
        insert_temp_interaction(args.provider_id, customer_id, args.temp_job_id)
        inserted = True

        status, body = api_get(profile_url, token)
        ok3 = status == 200 and "customer" in body and "stats" in body
        print(f"[3] profile with interaction: status={status} ok={ok3}")

        status, body = api_get(reviews_url, token)
        ok4 = status == 200 and "reviews" in body and "pagination" in body
        print(f"[4] reviews with interaction: status={status} ok={ok4}")

        # 3) invalid sort -> 400
        status, body = api_get(invalid_sort_url, token)
        ok5 = status == 400
        print(f"[5] reviews invalid sort: status={status} ok={ok5} body={body}")

        all_ok = ok1 and ok2 and ok3 and ok4 and ok5
        print(f"ALL_TESTS_PASS={all_ok}")
        return 0 if all_ok else 2
    finally:
        if inserted:
            cleanup_temp_interaction(args.provider_id, customer_id, args.temp_job_id)


if __name__ == "__main__":
    sys.exit(main())
