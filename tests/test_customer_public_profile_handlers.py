import importlib.util
import json
import os
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch


def _load_module(relative_path: str, module_name: str):
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    full_path = os.path.join(root, relative_path)
    spec = importlib.util.spec_from_file_location(module_name, full_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


profile_module = _load_module(
    "lambda/customers/get_customer_public_profile/handler.py",
    "get_customer_public_profile_handler",
)
reviews_module = _load_module(
    "lambda/customers/get_customer_public_reviews/handler.py",
    "get_customer_public_reviews_handler",
)


def _cursor_ctx(fetchone_values=None, fetchall_values=None):
    cm = MagicMock()
    cur = MagicMock()
    cm.__enter__.return_value = cur
    cm.__exit__.return_value = False

    fetchone_values = fetchone_values or []
    fetchall_values = fetchall_values or []
    cur.fetchone.side_effect = fetchone_values
    cur.fetchall.side_effect = fetchall_values
    return cm


def _base_event(customer_id="13"):
    return {
        "requestContext": {"authorizer": {"jwt": {"claims": {"sub": "provider-sub-123"}}}},
        "pathParameters": {"customer_id": customer_id},
    }


class TestCustomerPublicProfileHandler(unittest.TestCase):
    @patch.object(profile_module, "get_connection")
    def test_missing_identity_returns_401(self, mock_get_connection):
        response = profile_module.handler({}, None)
        self.assertEqual(response["statusCode"], 401)
        mock_get_connection.assert_not_called()

    @patch.object(profile_module, "get_connection")
    def test_invalid_customer_id_returns_400(self, mock_get_connection):
        response = profile_module.handler(_base_event(customer_id="abc"), None)
        self.assertEqual(response["statusCode"], 400)
        mock_get_connection.assert_not_called()

    @patch.object(profile_module, "can_provider_view_customer", return_value=(False, "Profile is private"))
    @patch.object(profile_module, "get_provider_id_from_sub", return_value="SP-001")
    @patch.object(profile_module, "get_connection")
    def test_private_profile_returns_403(self, mock_get_connection, _mock_provider, _mock_can_view):
        conn = MagicMock()
        mock_get_connection.return_value = conn

        response = profile_module.handler(_base_event(), None)
        body = json.loads(response["body"])
        self.assertEqual(response["statusCode"], 403)
        self.assertEqual(body["message"], "Profile is private")

    @patch.object(profile_module, "can_provider_view_customer", return_value=(False, "No prior interaction with this customer"))
    @patch.object(profile_module, "get_provider_id_from_sub", return_value="SP-001")
    @patch.object(profile_module, "get_connection")
    def test_restricted_without_interaction_returns_403(self, mock_get_connection, _mock_provider, _mock_can_view):
        conn = MagicMock()
        mock_get_connection.return_value = conn

        response = profile_module.handler(_base_event(), None)
        self.assertEqual(response["statusCode"], 403)

    @patch.object(profile_module, "upsert_customer_stats")
    @patch.object(profile_module, "calculate_customer_stats")
    @patch.object(profile_module, "is_stats_stale", return_value=False)
    @patch.object(profile_module, "can_provider_view_customer", return_value=(True, ""))
    @patch.object(profile_module, "get_provider_id_from_sub", return_value="SP-001")
    @patch.object(profile_module, "get_connection")
    def test_restricted_with_interaction_returns_200(
        self,
        mock_get_connection,
        _mock_provider,
        _mock_can_view,
        _mock_stale,
        mock_calc_stats,
        mock_upsert,
    ):
        conn = MagicMock()
        customer_row = {
            "customer_id": 13,
            "display_name": None,
            "first_name": "Test",
            "last_name": "Yang",
            "avatar_url": None,
            "created_at": datetime(2026, 1, 25, 1, 25, 55),
            "average_rating": 4.7,
        }
        cached_stats = {
            "customer_id": 13,
            "review_count": 2,
            "jobs_posted_6mo": 11,
            "jobs_completed": 10,
            "jobs_cancelled": 1,
            "completion_rate": 90.0,
            "cancellation_rate": 10.0,
            "avg_response_time_minutes": None,
            "last_updated": datetime.utcnow(),
        }
        recent_reviews = [{"review_id": 1, "rating": 5, "comment": "Great", "job_category": "Plumbing"}]
        categories = [{"category": "Plumbing", "count": 5}]

        conn.cursor.side_effect = [
            _cursor_ctx(fetchone_values=[customer_row]),
            _cursor_ctx(fetchone_values=[cached_stats]),
            _cursor_ctx(fetchall_values=[recent_reviews, categories]),
        ]
        mock_get_connection.return_value = conn

        response = profile_module.handler(_base_event(), None)
        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(body["customer"]["display_name"], "Test Y.")
        self.assertEqual(body["stats"]["avg_rating"], 4.7)
        self.assertEqual(len(body["recent_reviews"]), 1)
        self.assertTrue(any(b["type"] == "reliable" for b in body["badges"]))
        mock_calc_stats.assert_not_called()
        mock_upsert.assert_not_called()


class TestCustomerPublicReviewsHandler(unittest.TestCase):
    @patch.object(reviews_module, "get_connection")
    def test_invalid_sort_returns_400(self, mock_get_connection):
        event = _base_event()
        event["queryStringParameters"] = {"sort": "bad_sort"}
        response = reviews_module.handler(event, None)
        self.assertEqual(response["statusCode"], 400)
        mock_get_connection.assert_not_called()

    @patch.object(reviews_module, "can_provider_view_customer", return_value=(False, "No prior interaction with this customer"))
    @patch.object(reviews_module, "get_provider_id_from_sub", return_value="SP-001")
    @patch.object(reviews_module, "get_connection")
    def test_restricted_without_interaction_returns_403(self, mock_get_connection, _mock_provider, _mock_can_view):
        conn = MagicMock()
        mock_get_connection.return_value = conn

        response = reviews_module.handler(_base_event(), None)
        self.assertEqual(response["statusCode"], 403)

    @patch.object(reviews_module, "can_provider_view_customer", return_value=(True, ""))
    @patch.object(reviews_module, "get_provider_id_from_sub", return_value="SP-001")
    @patch.object(reviews_module, "get_connection")
    def test_restricted_with_interaction_returns_200_and_pagination(
        self, mock_get_connection, _mock_provider, _mock_can_view
    ):
        conn = MagicMock()
        rows = [
            {"review_id": 30, "rating": 5},
            {"review_id": 20, "rating": 4},
            {"review_id": 10, "rating": 3},
        ]
        conn.cursor.side_effect = [_cursor_ctx(fetchall_values=[rows])]
        mock_get_connection.return_value = conn

        event = _base_event()
        event["queryStringParameters"] = {"limit": "2", "sort": "recent"}
        response = reviews_module.handler(event, None)
        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(len(body["reviews"]), 2)
        self.assertTrue(body["pagination"]["has_more"])
        self.assertEqual(body["pagination"]["next_cursor"], 20)


if __name__ == "__main__":
    unittest.main()
