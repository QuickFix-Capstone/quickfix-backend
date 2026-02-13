#!/usr/bin/env python3
import importlib.util
import os
import unittest


def _load_handler_module():
    root = os.path.dirname(os.path.abspath(__file__))
    handler_path = os.path.join(root, "lambda", "jobs", "update_job_application", "handler.py")
    spec = importlib.util.spec_from_file_location("update_job_application_handler", handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class UpdateJobApplicationValidationTests(unittest.TestCase):
    def setUp(self):
        self.module = _load_handler_module()

    def test_parse_path_ids_requires_positive_ints(self):
        with self.assertRaises(ValueError):
            self.module._parse_path_ids({"pathParameters": {"job_id": "abc", "application_id": "1"}})
        with self.assertRaises(ValueError):
            self.module._parse_path_ids({"pathParameters": {"job_id": "1", "application_id": "0"}})

    def test_parse_updates_rejects_unknown_fields(self):
        with self.assertRaises(ValueError):
            self.module._parse_updates({"action": "accept"})

    def test_parse_updates_limits_message_length(self):
        with self.assertRaises(ValueError):
            self.module._parse_updates({"message": "x" * 1001})

    def test_parse_updates_accepts_valid_data(self):
        parsed = self.module._parse_updates({"proposed_price": "123.45", "message": "  hello  "})
        self.assertEqual(str(parsed["proposed_price"]), "123.45")
        self.assertEqual(parsed["message"], "hello")


if __name__ == "__main__":
    unittest.main()
