import os
import unittest
from unittest.mock import patch

import pandas as pd

from scripts import gemini_data_agent as agent


class GeminiDataAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        agent.configure_data(
            pd.DataFrame(
                {
                    "issued_at": pd.to_datetime(
                        ["2024-01-15", "2024-01-31", "2024-02-01"]
                    ),
                    "currency": ["EUR", "USD", "EUR"],
                    "payment_status": ["paid", "open", "paid"],
                    "analytics_net_amount_usd": [12.5, 20.0, 30.0],
                    "plan_name": ["Pro", "Pro", "Starter"],
                }
            ),
            "test data",
        )

    def test_get_sales_metrics_filters_plan_and_month(self) -> None:
        result = agent.get_sales_metrics("pro", "2024-01")

        self.assertEqual(result["invoice_count"], 2)
        self.assertEqual(result["paid_invoice_count"], 1)
        self.assertEqual(result["total_net_amount_usd"], 32.5)
        self.assertEqual(
            result["net_amount_usd_by_source_currency"], {"EUR": 12.5, "USD": 20.0}
        )

    def test_get_sales_metrics_returns_zeroes_for_empty_result(self) -> None:
        result = agent.get_sales_metrics("Enterprise", "2024-01")

        self.assertEqual(result["invoice_count"], 0)
        self.assertEqual(result["paid_invoice_count"], 0)
        self.assertEqual(result["total_net_amount_usd"], 0.0)
        self.assertEqual(result["net_amount_usd_by_source_currency"], {})

    def test_period_requires_supported_format(self) -> None:
        with self.assertRaisesRegex(ValueError, "period"):
            agent.get_sales_metrics("Pro", "January 2024")

    def test_database_url_uses_readonly_credentials(self) -> None:
        environment = {
            "READONLY_USER": "analytics_reader",
            "READONLY_PASSWORD": "reader/password",
            "POSTGRES_HOST": "localhost",
            "POSTGRES_PORT": "5433",
            "POSTGRES_DB": "torgdb",
        }
        with patch.dict(os.environ, environment, clear=True):
            database_url = agent.build_mart_database_url()

        self.assertEqual(database_url.username, "analytics_reader")
        self.assertEqual(database_url.host, "localhost")
        self.assertEqual(database_url.port, 5433)
        self.assertEqual(database_url.database, "torgdb")


if __name__ == "__main__":
    unittest.main()
