import importlib.util
import json
import os
import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch


def _load_module(relative_path: str, module_name: str):
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    full_path = os.path.join(root, relative_path)
    spec = importlib.util.spec_from_file_location(module_name, full_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


create_job_module = _load_module(
    "lambda/jobs/create_job/handler.py",
    "create_job_handler",
)


def _cursor_ctx(cursor: MagicMock):
    cm = MagicMock()
    cm.__enter__.return_value = cursor
    cm.__exit__.return_value = False
    return cm


class TestCreateJobHandler(unittest.TestCase):
    @patch.object(create_job_module, "get_connection")
    def test_handler_persists_and_returns_location_coordinates(self, mock_get_connection):
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value = _cursor_ctx(cursor)
        cursor.lastrowid = 321
        cursor.fetchone.side_effect = [
            {"customer_id": 77},
            {
                "job_id": 321,
                "customer_id": 77,
                "title": "Fix leaking kitchen sink",
                "description": "Sink has been leaking for 2 days, need urgent repair",
                "category": "plumber",
                "location_address": "123 Main St",
                "location_city": "Toronto",
                "location_state": "ON",
                "location_zip": "M5H 1J9",
                "location_lat": Decimal("43.6532000"),
                "location_lng": Decimal("-79.3832000"),
                "preferred_date": None,
                "preferred_time": None,
                "budget_min": Decimal("100.00"),
                "budget_max": Decimal("150.00"),
                "status": "open",
                "assigned_provider_id": None,
                "created_at": datetime(2026, 3, 25, 10, 0, 0),
                "updated_at": datetime(2026, 3, 25, 10, 0, 0),
            },
        ]
        mock_get_connection.return_value = conn

        event = {
            "requestContext": {
                "authorizer": {
                    "jwt": {
                        "claims": {
                            "sub": "customer-sub-123",
                        }
                    }
                }
            },
            "body": json.dumps(
                {
                    "title": "Fix leaking kitchen sink",
                    "description": "Sink has been leaking for 2 days, need urgent repair",
                    "category": "plumber",
                    "location_address": "123 Main St",
                    "location_city": "Toronto",
                    "location_state": "ON",
                    "location_zip": "M5H 1J9",
                    "location_lat": 43.6532,
                    "location_lng": -79.3832,
                    "budget_min": 100.0,
                    "budget_max": 150.0,
                }
            ),
        }

        response = create_job_module.handler(event, None)
        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 201)
        self.assertEqual(body["job"]["location"]["lat"], 43.6532)
        self.assertEqual(body["job"]["location"]["lng"], -79.3832)
        self.assertEqual(body["job"]["budget"]["min"], 100.0)
        self.assertEqual(body["job"]["budget"]["max"], 150.0)
        conn.commit.assert_called_once()

        insert_sql, insert_params = cursor.execute.call_args_list[1][0]
        self.assertIn("location_lat", insert_sql)
        self.assertIn("location_lng", insert_sql)
        self.assertEqual(insert_params[8], 43.6532)
        self.assertEqual(insert_params[9], -79.3832)


if __name__ == "__main__":
    unittest.main()
