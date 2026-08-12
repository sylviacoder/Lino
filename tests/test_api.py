from pathlib import Path
import sys
import json
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from lino_autocare_copilot.api import app, handler  # noqa: E402


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_health_endpoint(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "healthy",
                "service": "lino-autocare-copilot",
            },
        )

    def test_unsupported_question_does_not_call_bedrock(self):
        with patch(
            "lino_autocare_copilot.bedrock.boto3.client"
        ) as mock_bedrock_client:
            response = self.client.post(
                "/ask",
                json={
                    "question": "Who won the football match?",
                    "top_k": 3,
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["supported"])
        self.assertEqual(response.json()["sources"], [])
        mock_bedrock_client.assert_not_called()

    @patch("lino_autocare_copilot.api.generate_answer")
    def test_alignment_question_returns_grounded_source(
        self,
        mock_generate_answer,
    ):
        mock_generate_answer.return_value = (
            "Wheel alignment costs ₦3,000."
        )

        response = self.client.post(
            "/ask",
            json={
                "question": "How much does wheel alignment cost?",
                "top_k": 3,
            },
        )

        body = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(body["supported"])
        self.assertEqual(
            body["answer"],
            "Wheel alignment costs ₦3,000.",
        )
        self.assertEqual(body["sources"][0]["id"], "SERVICE-002")
        self.assertEqual(
            body["sources"][0]["price_status"],
            "user_confirmed_current",
        )
        mock_generate_answer.assert_called_once()

    def test_blank_question_is_rejected(self):
        response = self.client.post(
            "/ask",
            json={
                "question": "   ",
                "top_k": 3,
            },
        )

        self.assertEqual(response.status_code, 422)
        
    def test_lambda_handler_serves_health_endpoint(self):
        event = {
            "version": "2.0",
            "routeKey": "GET /health",
            "rawPath": "/health",
            "rawQueryString": "",
            "headers": {
                "host": "example.execute-api.us-east-1.amazonaws.com",
                "user-agent": "pytest",
                "x-forwarded-proto": "https",
            },
            "requestContext": {
                "accountId": "123456789012",
                "apiId": "test-api",
                "domainName": (
                    "example.execute-api.us-east-1.amazonaws.com"
                ),
                "domainPrefix": "example",
                "http": {
                    "method": "GET",
                    "path": "/health",
                    "protocol": "HTTP/1.1",
                    "sourceIp": "127.0.0.1",
                    "userAgent": "pytest",
                },
                "requestId": "test-request",
                "routeKey": "GET /health",
                "stage": "$default",
                "time": "12/Aug/2026:10:00:00 +0000",
                "timeEpoch": 1786528800000,
            },
            "isBase64Encoded": False,
        }

        response = handler(event, None)
        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(
            body,
            {
                "status": "healthy",
                "service": "lino-autocare-copilot",
            },
        )


if __name__ == "__main__":
    unittest.main()