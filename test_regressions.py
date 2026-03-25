import os
import tempfile
import unittest
import warnings

import numpy as np

from data import generate_financial_data, get_budget_config
from features import build_features
from inference import calculate_risk_score
from orchestrator import CFOOrchestrator


warnings.filterwarnings(
    "ignore",
    message="Non-stationary starting autoregressive parameters found.*",
    category=UserWarning,
)
warnings.filterwarnings(
    "ignore",
    message="Non-invertible starting MA parameters found.*",
    category=UserWarning,
)


class RegressionTests(unittest.TestCase):
    def test_burn_rate_is_seven_day_rolling_average(self):
        df = generate_financial_data(days=90)
        features = build_features(df, get_budget_config())

        daily_total = features["daily_spend_by_category"].sum(axis=1)
        expected = daily_total.rolling(window=7, min_periods=1).mean().to_numpy()

        self.assertTrue(np.allclose(features["burn_rate"], expected))

    def test_risk_score_respects_runway_coverage(self):
        critical_runway = calculate_risk_score(
            min_cash_projected=145000,
            current_cash=150000,
            days_to_risk=7,
            forecast_horizon_days=30,
        )
        buffered_runway = calculate_risk_score(
            min_cash_projected=145000,
            current_cash=300000,
            days_to_risk=30,
            forecast_horizon_days=30,
        )

        self.assertEqual(critical_runway, 1.0)
        self.assertLess(buffered_runway, 0.25)

    def test_orchestrator_core_inputs_change_outputs(self):
        base = CFOOrchestrator().run_analysis(days=90)
        checks = [
            (
                "current_cash",
                CFOOrchestrator(current_cash=300000).run_analysis(days=90),
                lambda result: result["cashflow_forecast"]["days_to_risk"],
            ),
            (
                "sector",
                CFOOrchestrator(sector="retail").run_analysis(days=90),
                lambda result: result["transaction_count"],
            ),
            (
                "business_scale",
                CFOOrchestrator(business_scale="enterprise").run_analysis(days=90),
                lambda result: result["transaction_count"],
            ),
            (
                "macro_environment",
                CFOOrchestrator(macro_environment="inflationary").run_analysis(days=90),
                lambda result: round(result["cashflow_forecast"]["projected_ending_cash"], 2),
            ),
            (
                "country",
                CFOOrchestrator(country="india").run_analysis(days=90),
                lambda result: result["transaction_count"],
            ),
            (
                "company_market_capital",
                CFOOrchestrator(company_market_capital=1500).run_analysis(days=90),
                lambda result: result["transaction_count"],
            ),
            (
                "funding_round",
                CFOOrchestrator(funding_round="public").run_analysis(days=90),
                lambda result: result["transaction_count"],
            ),
            (
                "state_of_business",
                CFOOrchestrator(state_of_business="growth").run_analysis(days=90),
                lambda result: result["transaction_count"],
            ),
            (
                "company_age_years",
                CFOOrchestrator(company_age_years=2).run_analysis(days=90),
                lambda result: result["transaction_count"],
            ),
            (
                "close_pressure",
                CFOOrchestrator(close_pressure="quarter_end").run_analysis(days=90),
                lambda result: result["compliance_analysis"]["kpis"]["review_queue"],
            ),
            (
                "planning_assumptions",
                CFOOrchestrator(
                    planning_assumptions={
                        "forecast_horizon_days": 60,
                        "burn_shock_pct": 0.15,
                        "collections_delay_days": 10,
                        "monte_carlo_sims": 400,
                        "revenue_outlook_pct": 0.10,
                        "hiring_growth_pct": 0.05,
                        "working_capital_efficiency": 0.10,
                        "capital_efficiency_score": 80,
                    }
                ).run_analysis(days=90),
                lambda result: round(result["cashflow_forecast"]["projected_ending_cash"], 2),
            ),
        ]

        for label, changed, getter in checks:
            with self.subTest(parameter=label):
                self.assertNotEqual(getter(base), getter(changed))

    def test_automation_maturity_changes_compliance_in_stressed_case(self):
        base_kwargs = {
            "current_cash": 80000,
            "close_pressure": "medium",
            "sector": "retail",
            "business_scale": "startup",
        }
        low_automation = CFOOrchestrator(
            automation_maturity="low",
            **base_kwargs,
        ).run_analysis(days=90)
        high_automation = CFOOrchestrator(
            automation_maturity="high",
            **base_kwargs,
        ).run_analysis(days=90)

        self.assertNotEqual(
            low_automation["compliance_analysis"]["kpis"]["auto_match_rate"],
            high_automation["compliance_analysis"]["kpis"]["auto_match_rate"],
        )
        self.assertNotEqual(
            low_automation["compliance_analysis"]["kpis"]["close_risk"],
            high_automation["compliance_analysis"]["kpis"]["close_risk"],
        )

    def test_zaggle_data_source_and_export_path_are_used(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as handle:
            handle.write("date,amount,vendor,category\n")
            handle.write("2026-03-01,1000,CloudHost,software\n")
            handle.write("2026-03-02,2500,Payroll Inc,payroll\n")
            handle.write("2026-03-03,800,OfficeMart,office\n")
            export_path = handle.name

        try:
            result = CFOOrchestrator(
                data_source="zaggle",
                zaggle_export_path=export_path,
            ).run_analysis(days=90)
        finally:
            os.remove(export_path)

        self.assertEqual(result["data_source"], "zaggle")
        self.assertEqual(result["data_source_status"], "connected")
        self.assertEqual(result["transaction_count"], 3)
        self.assertIn(export_path, result["data_source_message"])


if __name__ == "__main__":
    unittest.main()
