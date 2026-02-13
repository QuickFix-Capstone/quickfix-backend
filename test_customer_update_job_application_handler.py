#!/usr/bin/env python3
import importlib.util
import json
import os
import unittest
from datetime import datetime, timezone


def _load_handler_module():
    root = os.path.dirname(os.path.abspath(__file__))
    handler_path = os.path.join(
        root, "lambda", "jobs", "customer_update_job_application", "handler.py"
    )
    spec = importlib.util.spec_from_file_location("customer_update_job_application_handler", handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeCursor:
    def __init__(self, steps):
        self.steps = list(steps)
        self.current = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        if not self.steps:
            raise AssertionError(f"Unexpected SQL call: {sql} params={params}")
        step = self.steps.pop(0)
        if "contains" in step and step["contains"] not in sql:
            raise AssertionError(f"Expected SQL containing '{step['contains']}', got: {sql}")
        if "params" in step and step["params"] != params:
            raise AssertionError(f"Expected params {step['params']}, got {params}")
        self.current = step

    def fetchone(self):
        if not self.current:
            return None
        return self.current.get("fetchone")


class FakeConnection:
    def __init__(self, steps):
        self.steps = steps
        self.commits = 0
        self.closed = False

    def cursor(self):
        return FakeCursor(self.steps)

    def commit(self):
        self.commits += 1

    def close(self):
        self.closed = True


class CustomerUpdateJobApplicationTests(unittest.TestCase):
    def setUp(self):
        self.module = _load_handler_module()
        self.base_event = {
            "requestContext": {
                "authorizer": {
                    "jwt": {
                        "claims": {
                            "sub": "cust-sub-123",
                        }
                    }
                }
            },
            "pathParameters": {
                "job_id": "11",
                "application_id": "22",
            },
        }

    def test_parse_updates_rejects_unknown_fields(self):
        with self.assertRaises(ValueError):
            self.module._parse_updates({"status": "pending"})

    def test_success_updates_pending_application(self):
        now = datetime.now(timezone.utc).replace(microsecond=0)
        event = dict(self.base_event)
        event["body"] = json.dumps({"proposed_price": 199.99, "message": "Updated offer"})

        steps = [
            {
                "contains": "SELECT customer_id FROM customers",
                "params": ("cust-sub-123",),
                "fetchone": {"customer_id": 7},
            },
            {
                "contains": "SELECT job_id, customer_id, status FROM jobs",
                "params": (11,),
                "fetchone": {"job_id": 11, "customer_id": 7, "status": "open"},
            },
            {
                "contains": "FROM job_applications",
                "params": (22, 11),
                "fetchone": {
                    "application_id": 22,
                    "job_id": 11,
                    "provider_id": "SP-001",
                    "proposed_price": 150,
                    "message": "old",
                    "status": "pending",
                    "created_at": now,
                    "updated_at": now,
                    "customer_last_edited_at": None,
                },
            },
            {
                "contains": "UPDATE job_applications",
                "params": [self.module.Decimal("199.99"), "Updated offer", 22, 11],
            },
            {
                "contains": "FROM job_applications",
                "params": (22, 11),
                "fetchone": {
                    "application_id": 22,
                    "job_id": 11,
                    "provider_id": "SP-001",
                    "proposed_price": self.module.Decimal("199.99"),
                    "message": "Updated offer",
                    "status": "pending",
                    "created_at": now,
                    "updated_at": now,
                    "customer_last_edited_at": now,
                },
            },
        ]

        fake_conn = FakeConnection(steps)
        self.module.get_connection = lambda: fake_conn

        response = self.module.handler(event, None)
        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(body["application"]["proposed_price"], 199.99)
        self.assertEqual(body["application"]["message"], "Updated offer")
        self.assertEqual(fake_conn.commits, 1)

    def test_forbidden_when_customer_does_not_own_job(self):
        event = dict(self.base_event)
        event["body"] = json.dumps({"message": "Updated offer"})
        steps = [
            {
                "contains": "SELECT customer_id FROM customers",
                "params": ("cust-sub-123",),
                "fetchone": {"customer_id": 7},
            },
            {
                "contains": "SELECT job_id, customer_id, status FROM jobs",
                "params": (11,),
                "fetchone": {"job_id": 11, "customer_id": 9, "status": "open"},
            },
        ]
        fake_conn = FakeConnection(steps)
        self.module.get_connection = lambda: fake_conn

        response = self.module.handler(event, None)
        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 403)
        self.assertIn("own jobs", body["message"])


if __name__ == "__main__":
    unittest.main()
