"""
Decision Agent
Simulates multiple actions and recommends an optimal financial decision.
"""
from inference import monte_carlo_cashflow


class DecisionAgent:
    """
    Simulate multiple actions and recommend the best decision.
    This is the core agent for iterative decision-making.
    """

    BASE_ACTIONS = [
        {"name": "cut_marketing", "levels": [0.1, 0.2, 0.3]},
        {"name": "delay_vendor", "levels": [7, 14, 30]},
        {"name": "reduce_discretionary", "levels": [0.1, 0.2]},
        {"name": "do_nothing", "levels": [0]},
    ]
    SCENARIO_ACTIONS = {
        "saas": [
            {"name": "optimize_cloud", "levels": [0.1, 0.2]},
            {"name": "freeze_hiring", "levels": [0.05, 0.1]},
        ],
        "retail": [
            {"name": "rebalance_inventory", "levels": [0.1, 0.2]},
            {"name": "tighten_promotions", "levels": [0.1, 0.2]},
        ],
        "healthcare": [
            {"name": "optimize_staffing_mix", "levels": [0.05, 0.1]},
            {"name": "tighten_procurement", "levels": [0.1, 0.2]},
        ],
        "manufacturing": [
            {"name": "defer_capex", "levels": [0.1, 0.2]},
            {"name": "rebalance_inventory", "levels": [0.1, 0.2]},
        ],
        "fintech": [
            {"name": "optimize_cloud", "levels": [0.1, 0.2]},
            {"name": "consolidate_vendors", "levels": [0.1, 0.2]},
        ],
        "logistics": [
            {"name": "rebalance_inventory", "levels": [0.1, 0.2]},
            {"name": "tighten_procurement", "levels": [0.1, 0.2]},
        ],
        "hospitality": [
            {"name": "tighten_promotions", "levels": [0.1, 0.2]},
            {"name": "optimize_staffing_mix", "levels": [0.05, 0.1]},
        ],
        "education": [
            {"name": "optimize_staffing_mix", "levels": [0.05, 0.1]},
            {"name": "defer_capex", "levels": [0.1, 0.2]},
        ],
        "small_business": [
            {"name": "freeze_hiring", "levels": [0.05, 0.1]},
        ],
        "startup": [
            {"name": "freeze_hiring", "levels": [0.05, 0.1]},
        ],
        "enterprise": [
            {"name": "consolidate_vendors", "levels": [0.1, 0.2]},
            {"name": "defer_capex", "levels": [0.1, 0.2]},
        ],
        "large_enterprise": [
            {"name": "consolidate_vendors", "levels": [0.1, 0.2]},
            {"name": "defer_capex", "levels": [0.1, 0.2]},
            {"name": "tighten_procurement", "levels": [0.1, 0.2]},
        ],
    }

    def __init__(self, name="DecisionAgent"):
        self.name = name
        self.simulated_outcomes = []

    def make_decision(self, spend_analysis, forecast_analysis, features, budget_config):
        """
        Simulate multiple actions and recommend the best decision.

        Args:
            spend_analysis: Output from SpendIntelligenceAgent
            forecast_analysis: Output from CashFlowForecastAgent
            features: Features dict
            budget_config: Budget configuration

        Returns:
            Dict with decision analysis
        """
        return self.simulate_and_decide(
            spend_analysis,
            forecast_analysis,
            features,
            budget_config,
        )

    def simulate_and_decide(self, spend_analysis, forecast_analysis, features=None, budget_config=None):
        """
        Simulate every action/level combination and return the best option.

        The interface remains compatible with the orchestrator, while the
        decision logic now reflects CFO trade-offs beyond pure risk reduction.
        """
        baseline_risk = round(float(forecast_analysis["risk_score"]), 3)
        scenario_context = (features or {}).get("scenario_context", {})
        comparisons = []

        for action_config in self._get_available_actions(scenario_context):
            action_name = action_config["name"]
            for level in action_config["levels"]:
                simulation = self.simulate(
                    action_name,
                    level,
                    forecast_analysis,
                    spend_analysis,
                    scenario_context,
                )
                risk_reduction = max(0.0, baseline_risk - simulation["new_risk"])

                score = (
                    0.5 * risk_reduction
                    - 0.2 * simulation["cost"]
                    + 0.2 * simulation["feasibility"]
                    + 0.1 * simulation["reversibility"]
                )

                comparisons.append(
                    {
                        "action": action_name,
                        "level": level,
                        "level_display": self._format_level(action_name, level),
                        "risk_before": round(baseline_risk, 2),
                        "risk_after": round(simulation["new_risk"], 2),
                        "risk_reduction": round(risk_reduction, 2),
                        "business_cost": round(simulation["cost"], 2),
                        "feasibility": round(simulation["feasibility"], 2),
                        "reversibility": round(simulation["reversibility"], 2),
                        "score": round(score, 3),
                        "impact": self._get_impact_description(action_name, level, risk_reduction),
                    }
                )

        comparisons.sort(key=lambda item: item["score"], reverse=True)
        self.simulated_outcomes = comparisons

        best = comparisons[0] if comparisons else None
        second = comparisons[1] if len(comparisons) > 1 else best
        score_gap = (best["score"] - second["score"]) if best and second else 0.0
        confidence = min(1.0, max(0.0, round(score_gap * 5, 3)))

        best_action = best["action"] if best else None
        best_level = best["level"] if best else None
        reasoning = self._build_reasoning(best, second, spend_analysis, forecast_analysis, scenario_context)

        return {
            "best_action": best_action,
            "level": best_level,
            "level_display": self._format_level(best_action, best_level) if best else None,
            "confidence": confidence,
            "comparisons": comparisons[:5],
            "reasoning": reasoning,
            "risk_reduction": best["risk_reduction"] if best else 0,
        }

    def simulate(self, action, level, forecast, spend, scenario_context=None):
        """
        Simulate a specific action/level combination.

        Returns normalized business trade-off metrics in the 0-1 range.
        """
        base_risk = float(forecast.get("risk_score", 0))
        days_to_risk = max(1, int(forecast.get("days_to_risk", 30)))
        spend_category = spend.get("category")
        spend_severity = spend.get("severity", "low")
        percent_change = abs(float(spend.get("percent_change", 0)))
        scenario_context = scenario_context or {}
        sector = scenario_context.get("sector", "saas")
        business_scale = scenario_context.get("business_scale", "mid_market")
        macro_environment = scenario_context.get("macro_environment", "stable")
        country = scenario_context.get("country", "united_states")
        company_market_capital = float(scenario_context.get("company_market_capital", 500))
        funding_round = scenario_context.get("funding_round", "series_a")
        state_of_business = scenario_context.get("state_of_business", "profit")
        company_age_years = float(scenario_context.get("company_age_years", 5))
        capital_efficiency_score = float(scenario_context.get("capital_efficiency_score", 50))

        severity_factor = {
            "low": 0.15,
            "medium": 0.35,
            "high": 0.55,
            "critical": 0.75,
        }.get(spend_severity, 0.25)
        anomaly_factor = min(0.25, percent_change / 1000)
        sector_adjustments = self._get_sector_action_adjustments(
            sector,
            business_scale,
            macro_environment,
            country,
            company_market_capital,
            funding_round,
            state_of_business,
            company_age_years,
            capital_efficiency_score,
        )
        action_adjustment = sector_adjustments.get(action, {})

        if action == "cut_marketing":
            # Lower marketing spend helps near-term cash, but deeper cuts create
            # more commercial drag even if they are relatively easy to reverse.
            urgency_bonus = 0.08 if days_to_risk < 14 else 0.03
            focus_bonus = 0.05 if spend_category == "marketing" else 0.0
            risk_reduction = min(
                base_risk,
                base_risk * (
                    0.35 * level
                    + urgency_bonus
                    + focus_bonus
                    + anomaly_factor
                    + action_adjustment.get("risk_bonus", 0.0)
                )
            )
            business_cost = min(
                1.0,
                0.22 + (1.45 * level) + (0.12 if spend_category == "marketing" else 0.0)
                + action_adjustment.get("cost_penalty", 0.0)
            )
            feasibility = max(0.0, 0.9 - (0.7 * level) + action_adjustment.get("feasibility_bonus", 0.0))
            reversibility = max(0.0, 0.88 - (0.3 * level) + action_adjustment.get("reversibility_bonus", 0.0))

        elif action == "delay_vendor":
            # Payment delays create immediate liquidity relief, but the trade-off
            # is supplier friction and lower reversibility at longer durations.
            delay_ratio = min(1.0, level / 30)
            urgency_bonus = 0.1 if days_to_risk < 10 else 0.04
            risk_reduction = min(
                base_risk,
                base_risk * (
                    0.25
                    + (0.45 * delay_ratio)
                    + urgency_bonus
                    + (0.08 * severity_factor)
                    + action_adjustment.get("risk_bonus", 0.0)
                )
            )
            business_cost = min(1.0, 0.28 + (0.42 * delay_ratio) + action_adjustment.get("cost_penalty", 0.0))
            feasibility = max(0.0, 0.82 - (0.22 * delay_ratio) + action_adjustment.get("feasibility_bonus", 0.0))
            reversibility = max(0.0, 0.42 - (0.24 * delay_ratio) + action_adjustment.get("reversibility_bonus", 0.0))

        elif action == "reduce_discretionary":
            # Discretionary cuts are usually easier to implement and unwind, but
            # the cash impact is smaller than more aggressive interventions.
            focus_bonus = 0.05 if spend_category in {"operations", "travel", "software"} else 0.0
            risk_reduction = min(
                base_risk,
                base_risk * (
                    0.28 * level
                    + 0.06
                    + focus_bonus
                    + (0.06 * severity_factor)
                    + action_adjustment.get("risk_bonus", 0.0)
                )
            )
            business_cost = min(1.0, 0.1 + (0.6 * level) + action_adjustment.get("cost_penalty", 0.0))
            feasibility = max(0.0, 0.92 - (0.35 * level) + action_adjustment.get("feasibility_bonus", 0.0))
            reversibility = max(0.0, 0.94 - (0.18 * level) + action_adjustment.get("reversibility_bonus", 0.0))

        elif action == "optimize_cloud":
            risk_reduction = min(
                base_risk,
                base_risk * (0.22 + (0.35 * level) + (0.05 * severity_factor) + action_adjustment.get("risk_bonus", 0.0))
            )
            business_cost = min(1.0, 0.08 + (0.35 * level) + action_adjustment.get("cost_penalty", 0.0))
            feasibility = max(0.0, 0.88 - (0.25 * level) + action_adjustment.get("feasibility_bonus", 0.0))
            reversibility = max(0.0, 0.9 - (0.12 * level) + action_adjustment.get("reversibility_bonus", 0.0))

        elif action == "freeze_hiring":
            risk_reduction = min(
                base_risk,
                base_risk * (0.18 + (0.55 * level) + (0.04 * severity_factor) + action_adjustment.get("risk_bonus", 0.0))
            )
            business_cost = min(1.0, 0.18 + (0.65 * level) + action_adjustment.get("cost_penalty", 0.0))
            feasibility = max(0.0, 0.84 - (0.3 * level) + action_adjustment.get("feasibility_bonus", 0.0))
            reversibility = max(0.0, 0.76 - (0.2 * level) + action_adjustment.get("reversibility_bonus", 0.0))

        elif action == "rebalance_inventory":
            risk_reduction = min(
                base_risk,
                base_risk * (0.2 + (0.4 * level) + (0.06 * severity_factor) + action_adjustment.get("risk_bonus", 0.0))
            )
            business_cost = min(1.0, 0.14 + (0.42 * level) + action_adjustment.get("cost_penalty", 0.0))
            feasibility = max(0.0, 0.82 - (0.22 * level) + action_adjustment.get("feasibility_bonus", 0.0))
            reversibility = max(0.0, 0.72 - (0.25 * level) + action_adjustment.get("reversibility_bonus", 0.0))

        elif action == "tighten_promotions":
            risk_reduction = min(
                base_risk,
                base_risk * (0.16 + (0.32 * level) + anomaly_factor + action_adjustment.get("risk_bonus", 0.0))
            )
            business_cost = min(1.0, 0.16 + (0.5 * level) + action_adjustment.get("cost_penalty", 0.0))
            feasibility = max(0.0, 0.86 - (0.24 * level) + action_adjustment.get("feasibility_bonus", 0.0))
            reversibility = max(0.0, 0.83 - (0.18 * level) + action_adjustment.get("reversibility_bonus", 0.0))

        elif action == "optimize_staffing_mix":
            risk_reduction = min(
                base_risk,
                base_risk * (0.18 + (0.45 * level) + (0.07 * severity_factor) + action_adjustment.get("risk_bonus", 0.0))
            )
            business_cost = min(1.0, 0.15 + (0.48 * level) + action_adjustment.get("cost_penalty", 0.0))
            feasibility = max(0.0, 0.78 - (0.28 * level) + action_adjustment.get("feasibility_bonus", 0.0))
            reversibility = max(0.0, 0.7 - (0.22 * level) + action_adjustment.get("reversibility_bonus", 0.0))

        elif action == "tighten_procurement":
            risk_reduction = min(
                base_risk,
                base_risk * (0.18 + (0.34 * level) + (0.08 * severity_factor) + action_adjustment.get("risk_bonus", 0.0))
            )
            business_cost = min(1.0, 0.12 + (0.32 * level) + action_adjustment.get("cost_penalty", 0.0))
            feasibility = max(0.0, 0.83 - (0.18 * level) + action_adjustment.get("feasibility_bonus", 0.0))
            reversibility = max(0.0, 0.81 - (0.12 * level) + action_adjustment.get("reversibility_bonus", 0.0))

        elif action == "defer_capex":
            risk_reduction = min(
                base_risk,
                base_risk * (0.24 + (0.46 * level) + action_adjustment.get("risk_bonus", 0.0))
            )
            business_cost = min(1.0, 0.13 + (0.28 * level) + action_adjustment.get("cost_penalty", 0.0))
            feasibility = max(0.0, 0.8 - (0.18 * level) + action_adjustment.get("feasibility_bonus", 0.0))
            reversibility = max(0.0, 0.68 - (0.22 * level) + action_adjustment.get("reversibility_bonus", 0.0))

        elif action == "consolidate_vendors":
            risk_reduction = min(
                base_risk,
                base_risk * (0.17 + (0.3 * level) + (0.04 * severity_factor) + action_adjustment.get("risk_bonus", 0.0))
            )
            business_cost = min(1.0, 0.1 + (0.26 * level) + action_adjustment.get("cost_penalty", 0.0))
            feasibility = max(0.0, 0.76 - (0.16 * level) + action_adjustment.get("feasibility_bonus", 0.0))
            reversibility = max(0.0, 0.74 - (0.1 * level) + action_adjustment.get("reversibility_bonus", 0.0))

        else:
            risk_reduction = 0.0
            business_cost = 0.0
            feasibility = 0.0
            reversibility = 0.0

        new_risk = max(0.0, base_risk - risk_reduction)

        return {
            "new_risk": round(new_risk, 4),
            "cost": round(business_cost, 4),
            "feasibility": round(feasibility, 4),
            "reversibility": round(reversibility, 4),
        }

    def _get_available_actions(self, scenario_context):
        """Build the action set relevant to the current sector and company size."""
        scenario_context = scenario_context or {}
        sector = scenario_context.get("sector")
        business_scale = scenario_context.get("business_scale")

        actions = list(self.BASE_ACTIONS)
        seen = {action["name"] for action in actions}

        for key in (sector, business_scale):
            for action in self.SCENARIO_ACTIONS.get(key, []):
                if action["name"] not in seen:
                    actions.append(action)
                    seen.add(action["name"])

        return actions

    def _get_sector_action_adjustments(
        self,
        sector,
        business_scale,
        macro_environment,
        country,
        company_market_capital,
        funding_round,
        state_of_business,
        company_age_years,
        capital_efficiency_score,
    ):
        """Apply sector and scale-specific business trade-offs to each action."""
        base = {
            "cut_marketing": {"risk_bonus": 0.0, "cost_penalty": 0.0, "feasibility_bonus": 0.0, "reversibility_bonus": 0.0},
            "delay_vendor": {"risk_bonus": 0.0, "cost_penalty": 0.0, "feasibility_bonus": 0.0, "reversibility_bonus": 0.0},
            "reduce_discretionary": {"risk_bonus": 0.0, "cost_penalty": 0.0, "feasibility_bonus": 0.0, "reversibility_bonus": 0.0},
            "optimize_cloud": {"risk_bonus": 0.0, "cost_penalty": 0.0, "feasibility_bonus": 0.0, "reversibility_bonus": 0.0},
            "freeze_hiring": {"risk_bonus": 0.0, "cost_penalty": 0.0, "feasibility_bonus": 0.0, "reversibility_bonus": 0.0},
            "rebalance_inventory": {"risk_bonus": 0.0, "cost_penalty": 0.0, "feasibility_bonus": 0.0, "reversibility_bonus": 0.0},
            "tighten_promotions": {"risk_bonus": 0.0, "cost_penalty": 0.0, "feasibility_bonus": 0.0, "reversibility_bonus": 0.0},
            "optimize_staffing_mix": {"risk_bonus": 0.0, "cost_penalty": 0.0, "feasibility_bonus": 0.0, "reversibility_bonus": 0.0},
            "tighten_procurement": {"risk_bonus": 0.0, "cost_penalty": 0.0, "feasibility_bonus": 0.0, "reversibility_bonus": 0.0},
            "defer_capex": {"risk_bonus": 0.0, "cost_penalty": 0.0, "feasibility_bonus": 0.0, "reversibility_bonus": 0.0},
            "consolidate_vendors": {"risk_bonus": 0.0, "cost_penalty": 0.0, "feasibility_bonus": 0.0, "reversibility_bonus": 0.0},
        }

        sector_profiles = {
            "saas": {
                "cut_marketing": {"risk_bonus": 0.08, "cost_penalty": -0.06, "feasibility_bonus": 0.05},
                "delay_vendor": {"cost_penalty": 0.08, "reversibility_bonus": -0.05},
                "reduce_discretionary": {"risk_bonus": 0.03, "feasibility_bonus": 0.04},
                "optimize_cloud": {"risk_bonus": 0.14, "cost_penalty": -0.05, "feasibility_bonus": 0.08},
                "freeze_hiring": {"risk_bonus": 0.06, "feasibility_bonus": 0.03},
            },
            "retail": {
                "cut_marketing": {"cost_penalty": 0.12, "feasibility_bonus": -0.05},
                "delay_vendor": {"cost_penalty": 0.18, "feasibility_bonus": -0.08, "reversibility_bonus": -0.08},
                "reduce_discretionary": {"risk_bonus": 0.09, "cost_penalty": -0.03, "feasibility_bonus": 0.06},
                "rebalance_inventory": {"risk_bonus": 0.15, "cost_penalty": -0.04, "feasibility_bonus": 0.07},
                "tighten_promotions": {"risk_bonus": 0.08, "feasibility_bonus": 0.05},
            },
            "healthcare": {
                "cut_marketing": {"cost_penalty": 0.04},
                "delay_vendor": {"cost_penalty": 0.22, "feasibility_bonus": -0.1, "reversibility_bonus": -0.1},
                "reduce_discretionary": {"risk_bonus": 0.1, "cost_penalty": -0.04, "feasibility_bonus": 0.07},
                "optimize_staffing_mix": {"risk_bonus": 0.14, "cost_penalty": -0.02, "feasibility_bonus": 0.06},
                "tighten_procurement": {"risk_bonus": 0.11, "feasibility_bonus": 0.05},
            },
            "manufacturing": {
                "cut_marketing": {"cost_penalty": 0.08, "feasibility_bonus": -0.04},
                "delay_vendor": {"cost_penalty": 0.2, "feasibility_bonus": -0.1, "reversibility_bonus": -0.12},
                "reduce_discretionary": {"risk_bonus": 0.08, "cost_penalty": -0.02, "feasibility_bonus": 0.05},
                "defer_capex": {"risk_bonus": 0.14, "cost_penalty": -0.05, "feasibility_bonus": 0.07},
                "rebalance_inventory": {"risk_bonus": 0.12, "feasibility_bonus": 0.05},
            },
            "fintech": {
                "cut_marketing": {"cost_penalty": 0.02, "feasibility_bonus": 0.02},
                "delay_vendor": {"cost_penalty": 0.12, "reversibility_bonus": -0.06},
                "reduce_discretionary": {"risk_bonus": 0.05, "feasibility_bonus": 0.03},
                "optimize_cloud": {"risk_bonus": 0.16, "cost_penalty": -0.06, "feasibility_bonus": 0.09},
                "consolidate_vendors": {"risk_bonus": 0.08, "cost_penalty": -0.02, "feasibility_bonus": 0.06},
            },
            "logistics": {
                "cut_marketing": {"cost_penalty": 0.1, "feasibility_bonus": -0.03},
                "delay_vendor": {"cost_penalty": 0.21, "feasibility_bonus": -0.1, "reversibility_bonus": -0.1},
                "reduce_discretionary": {"risk_bonus": 0.07, "feasibility_bonus": 0.04},
                "rebalance_inventory": {"risk_bonus": 0.16, "cost_penalty": -0.05, "feasibility_bonus": 0.08},
                "tighten_procurement": {"risk_bonus": 0.13, "cost_penalty": -0.03, "feasibility_bonus": 0.07},
            },
            "hospitality": {
                "cut_marketing": {"cost_penalty": 0.15, "feasibility_bonus": -0.06},
                "delay_vendor": {"cost_penalty": 0.16, "feasibility_bonus": -0.06, "reversibility_bonus": -0.08},
                "reduce_discretionary": {"risk_bonus": 0.1, "cost_penalty": -0.02, "feasibility_bonus": 0.06},
                "tighten_promotions": {"risk_bonus": 0.12, "cost_penalty": -0.02, "feasibility_bonus": 0.08},
                "optimize_staffing_mix": {"risk_bonus": 0.15, "cost_penalty": -0.01, "feasibility_bonus": 0.07},
            },
            "education": {
                "cut_marketing": {"cost_penalty": 0.03},
                "delay_vendor": {"cost_penalty": 0.14, "feasibility_bonus": -0.07, "reversibility_bonus": -0.07},
                "reduce_discretionary": {"risk_bonus": 0.06, "feasibility_bonus": 0.05},
                "optimize_staffing_mix": {"risk_bonus": 0.16, "cost_penalty": -0.03, "feasibility_bonus": 0.08},
                "defer_capex": {"risk_bonus": 0.11, "cost_penalty": -0.02, "feasibility_bonus": 0.07},
            },
        }
        scale_profiles = {
            "small_business": {
                "cut_marketing": {"feasibility_bonus": 0.05, "cost_penalty": -0.03},
                "delay_vendor": {"cost_penalty": 0.14, "feasibility_bonus": -0.09, "reversibility_bonus": -0.06},
                "reduce_discretionary": {"risk_bonus": 0.07, "feasibility_bonus": 0.05},
                "freeze_hiring": {"risk_bonus": 0.12, "cost_penalty": -0.05, "feasibility_bonus": 0.09},
            },
            "startup": {
                "cut_marketing": {"feasibility_bonus": 0.04, "cost_penalty": -0.02},
                "delay_vendor": {"cost_penalty": 0.12, "feasibility_bonus": -0.08, "reversibility_bonus": -0.05},
                "reduce_discretionary": {"risk_bonus": 0.05, "feasibility_bonus": 0.04},
                "freeze_hiring": {"risk_bonus": 0.1, "cost_penalty": -0.04, "feasibility_bonus": 0.08},
            },
            "mid_market": {},
            "enterprise": {
                "cut_marketing": {"cost_penalty": 0.04},
                "delay_vendor": {"risk_bonus": 0.03, "feasibility_bonus": 0.03},
                "reduce_discretionary": {"cost_penalty": 0.02},
                "consolidate_vendors": {"risk_bonus": 0.1, "cost_penalty": -0.03, "feasibility_bonus": 0.08},
                "defer_capex": {"risk_bonus": 0.08, "feasibility_bonus": 0.06},
            },
            "large_enterprise": {
                "cut_marketing": {"cost_penalty": 0.05},
                "delay_vendor": {"risk_bonus": 0.04, "cost_penalty": 0.04, "feasibility_bonus": 0.04},
                "reduce_discretionary": {"cost_penalty": 0.03},
                "consolidate_vendors": {"risk_bonus": 0.14, "cost_penalty": -0.04, "feasibility_bonus": 0.1},
                "defer_capex": {"risk_bonus": 0.12, "feasibility_bonus": 0.08},
                "tighten_procurement": {"risk_bonus": 0.11, "cost_penalty": -0.03, "feasibility_bonus": 0.08},
            },
        }
        macro_profiles = {
            "stable": {},
            "inflationary": {
                "cut_marketing": {"cost_penalty": 0.05},
                "delay_vendor": {"risk_bonus": 0.03, "cost_penalty": 0.08, "feasibility_bonus": -0.02, "reversibility_bonus": -0.04},
                "reduce_discretionary": {"risk_bonus": 0.12, "cost_penalty": -0.03, "feasibility_bonus": 0.06},
            },
            "recessionary": {
                "cut_marketing": {"risk_bonus": 0.07, "cost_penalty": -0.04, "feasibility_bonus": 0.04},
                "delay_vendor": {"cost_penalty": 0.08, "reversibility_bonus": -0.06},
                "reduce_discretionary": {"risk_bonus": 0.12, "cost_penalty": -0.05, "feasibility_bonus": 0.08},
            },
        }
        country_profiles = {
            "united_states": {
                "cut_marketing": {"feasibility_bonus": 0.03},
                "optimize_cloud": {"risk_bonus": 0.05, "feasibility_bonus": 0.04},
            },
            "india": {
                "reduce_discretionary": {"risk_bonus": 0.06, "cost_penalty": -0.02},
                "delay_vendor": {"cost_penalty": 0.05},
            },
            "singapore": {
                "consolidate_vendors": {"risk_bonus": 0.05, "feasibility_bonus": 0.04},
                "tighten_procurement": {"risk_bonus": 0.04, "feasibility_bonus": 0.03},
            },
            "united_kingdom": {
                "cut_marketing": {"cost_penalty": 0.02},
                "defer_capex": {"risk_bonus": 0.04},
            },
            "uae": {
                "delay_vendor": {"risk_bonus": 0.02, "feasibility_bonus": 0.02},
                "reduce_discretionary": {"feasibility_bonus": 0.03},
            },
            "germany": {
                "tighten_procurement": {"risk_bonus": 0.06, "feasibility_bonus": 0.04},
                "delay_vendor": {"cost_penalty": 0.07, "reversibility_bonus": -0.03},
            },
        }
        funding_profiles = {
            "bootstrapped": {
                "freeze_hiring": {"risk_bonus": 0.12, "cost_penalty": -0.04, "feasibility_bonus": 0.08},
                "reduce_discretionary": {"risk_bonus": 0.08, "feasibility_bonus": 0.05},
            },
            "seed": {
                "freeze_hiring": {"risk_bonus": 0.09, "feasibility_bonus": 0.06},
                "cut_marketing": {"feasibility_bonus": 0.03},
            },
            "series_a": {},
            "series_b": {
                "optimize_cloud": {"risk_bonus": 0.05, "feasibility_bonus": 0.03},
                "defer_capex": {"risk_bonus": 0.04, "feasibility_bonus": 0.03},
            },
            "series_c": {
                "consolidate_vendors": {"risk_bonus": 0.06, "feasibility_bonus": 0.04},
                "defer_capex": {"risk_bonus": 0.05, "feasibility_bonus": 0.04},
            },
            "public": {
                "consolidate_vendors": {"risk_bonus": 0.08, "cost_penalty": -0.03, "feasibility_bonus": 0.05},
                "tighten_procurement": {"risk_bonus": 0.07, "feasibility_bonus": 0.05},
            },
        }
        state_profiles = {
            "survival": {
                "freeze_hiring": {"risk_bonus": 0.1, "feasibility_bonus": 0.06},
                "reduce_discretionary": {"risk_bonus": 0.09, "feasibility_bonus": 0.05},
                "delay_vendor": {"risk_bonus": 0.03, "cost_penalty": 0.02},
            },
            "profit": {
                "optimize_cloud": {"risk_bonus": 0.04, "feasibility_bonus": 0.03},
                "tighten_procurement": {"risk_bonus": 0.05, "feasibility_bonus": 0.04},
            },
            "growth": {
                "cut_marketing": {"cost_penalty": 0.08},
                "delay_vendor": {"cost_penalty": 0.08, "reversibility_bonus": -0.04},
                "do_nothing": {"risk_bonus": 0.03},
            },
        }

        market_cap_profile = {}
        if company_market_capital < 250:
            market_cap_profile = {
                "freeze_hiring": {"risk_bonus": 0.08, "feasibility_bonus": 0.05},
                "reduce_discretionary": {"risk_bonus": 0.06, "feasibility_bonus": 0.04},
            }
        elif company_market_capital > 1000:
            market_cap_profile = {
                "optimize_cloud": {"risk_bonus": 0.05, "feasibility_bonus": 0.04},
                "consolidate_vendors": {"risk_bonus": 0.05, "feasibility_bonus": 0.04},
            }
        age_profile = {}
        if company_age_years <= 3:
            age_profile = {
                "freeze_hiring": {"risk_bonus": 0.08, "feasibility_bonus": 0.05},
                "cut_marketing": {"feasibility_bonus": 0.05},
            }
        elif company_age_years >= 12:
            age_profile = {
                "consolidate_vendors": {"risk_bonus": 0.07, "feasibility_bonus": 0.05},
                "defer_capex": {"risk_bonus": 0.05, "feasibility_bonus": 0.04},
            }

        capital_efficiency_profile = {}
        if capital_efficiency_score < 40:
            capital_efficiency_profile = {
                "optimize_cloud": {"risk_bonus": 0.08, "feasibility_bonus": 0.05},
                "reduce_discretionary": {"risk_bonus": 0.07, "feasibility_bonus": 0.05},
                "freeze_hiring": {"risk_bonus": 0.07, "feasibility_bonus": 0.05},
            }
        elif capital_efficiency_score > 70:
            capital_efficiency_profile = {
                "do_nothing": {"risk_bonus": 0.02},
                "delay_vendor": {"cost_penalty": 0.04},
                "reduce_discretionary": {"cost_penalty": 0.03},
            }

        for profile in (
            sector_profiles.get(sector, {}),
            scale_profiles.get(business_scale, {}),
            macro_profiles.get(macro_environment, {}),
            country_profiles.get(country, {}),
            funding_profiles.get(funding_round, {}),
            state_profiles.get(state_of_business, {}),
            market_cap_profile,
            age_profile,
            capital_efficiency_profile,
        ):
            for action, adjustments in profile.items():
                if action not in base:
                    continue
                for key, value in adjustments.items():
                    base[action][key] = base[action].get(key, 0.0) + value

        return base

    def _get_impact_description(self, action, level, risk_reduction):
        """Get a human-readable impact description."""
        pct_reduction = risk_reduction * 100

        if action == "do_nothing":
            return "Maintain current trajectory with no near-term intervention."
        if action == "cut_marketing":
            return (
                f"Cut marketing by {int(level * 100)}% to lower burn, with "
                f"an estimated {pct_reduction:.0f}% risk reduction and higher long-term commercial cost."
            )
        if action == "delay_vendor":
            return (
                f"Delay vendor payments by {level} days to preserve cash, "
                f"reducing risk by about {pct_reduction:.0f}% but weakening reversibility."
            )
        if action == "reduce_discretionary":
            return (
                f"Reduce discretionary spend by {int(level * 100)}% for a modest "
                f"{pct_reduction:.0f}% risk reduction with limited business disruption."
            )
        if action == "optimize_cloud":
            return f"Optimize cloud and software usage by {int(level * 100)}%, reducing technical run-rate and risk by ~{pct_reduction:.0f}%."
        if action == "freeze_hiring":
            return f"Freeze hiring growth by {int(level * 100)}%, slowing payroll expansion and lowering risk by ~{pct_reduction:.0f}%."
        if action == "rebalance_inventory":
            return f"Rebalance inventory by {int(level * 100)}% to free working capital and lower risk by ~{pct_reduction:.0f}%."
        if action == "tighten_promotions":
            return f"Tighten promotional intensity by {int(level * 100)}% to protect margin and reduce risk by ~{pct_reduction:.0f}%."
        if action == "optimize_staffing_mix":
            return f"Optimize staffing mix by {int(level * 100)}% to improve labor efficiency and reduce risk by ~{pct_reduction:.0f}%."
        if action == "tighten_procurement":
            return f"Tighten procurement controls by {int(level * 100)}% to lower supply spend volatility and reduce risk by ~{pct_reduction:.0f}%."
        if action == "defer_capex":
            return f"Defer capital expenditure by {int(level * 100)}% to preserve cash and reduce risk by ~{pct_reduction:.0f}%."
        if action == "consolidate_vendors":
            return f"Consolidate vendor spend by {int(level * 100)}% to improve pricing leverage and reduce risk by ~{pct_reduction:.0f}%."
        return "Unknown action."

    def _build_reasoning(self, best, second, spend_analysis, forecast_analysis, scenario_context=None):
        """Build reasoning for the recommended action and level."""
        if not best:
            return "No actionable simulation results were generated."

        action = best["action"]
        level = best["level"]
        action_text = self._format_action(action, level)
        score_gap = best["score"] - second["score"] if second else best["score"]
        sector = (scenario_context or {}).get("sector")
        macro_environment = (scenario_context or {}).get("macro_environment")

        if forecast_analysis["risk_level"] == "critical":
            return (
                f"Liquidity risk is critical, so the engine prioritizes near-term cash preservation. "
                f"{action_text} offers the strongest trade-off between risk reduction and execution cost."
            )
        if action == "delay_vendor":
            return (
                f"{action_text} is favored because it improves short-term liquidity more than the alternatives, "
                f"despite lower reversibility. Score gap vs. next option: {score_gap:.2f}."
            )
        if action == "cut_marketing":
            return (
                f"{action_text} is the best balance of risk reduction and feasibility for the "
                f"{macro_environment or 'current'} {sector or 'business'} scenario. "
                f"The model accepts some growth impact because current cash pressure outweighs the long-term cost."
            )
        if action == "reduce_discretionary":
            return (
                f"{action_text} is preferred because it preserves flexibility while still lowering risk in the "
                f"{macro_environment or 'current'} {sector or 'current'} operating model. "
                f"It outperforms more disruptive options on feasibility and reversibility."
            )
        if action in {"optimize_cloud", "tighten_procurement", "rebalance_inventory", "defer_capex", "freeze_hiring", "consolidate_vendors", "optimize_staffing_mix", "tighten_promotions"}:
            return (
                f"{action_text} is favored because it is more specific to the {sector or 'current'} "
                f"{scenario_context.get('business_scale', 'business')} context than the generic alternatives. "
                f"Score gap vs. next option: {score_gap:.2f}."
            )
        return f"No intervention clearly dominates, so the engine recommends maintaining the current plan."

    def _format_action(self, action, level):
        """Format action/level into a readable recommendation."""
        level_text = self._format_level(action, level)

        if action == "cut_marketing":
            return f"Cut marketing by {level_text}"
        if action == "delay_vendor":
            return f"Delay vendor payments by {level_text}"
        if action == "reduce_discretionary":
            return f"Reduce discretionary spend by {level_text}"
        if action == "optimize_cloud":
            return f"Optimize cloud spend by {level_text}"
        if action == "freeze_hiring":
            return f"Freeze hiring by {level_text}"
        if action == "rebalance_inventory":
            return f"Rebalance inventory by {level_text}"
        if action == "tighten_promotions":
            return f"Tighten promotions by {level_text}"
        if action == "optimize_staffing_mix":
            return f"Optimize staffing mix by {level_text}"
        if action == "tighten_procurement":
            return f"Tighten procurement by {level_text}"
        if action == "defer_capex":
            return f"Defer capex by {level_text}"
        if action == "consolidate_vendors":
            return f"Consolidate vendors by {level_text}"
        return "Do nothing"

    def _format_level(self, action, level):
        """Format a level for UI and narrative output."""
        if action in {
            "cut_marketing",
            "reduce_discretionary",
            "optimize_cloud",
            "freeze_hiring",
            "rebalance_inventory",
            "tighten_promotions",
            "optimize_staffing_mix",
            "tighten_procurement",
            "defer_capex",
            "consolidate_vendors",
        }:
            return f"{int(level * 100)}%"
        if action == "delay_vendor":
            return f"{level} days"
        return "0"

    def get_context(self):
        """Get agent context for orchestrator."""
        return {
            "name": self.name,
            "role": "Decision Making",
            "responsibility": "Simulate actions and recommend optimal decision",
        }

    def get_available_actions(self, scenario_context=None):
        """Return UI-friendly available actions for the current scenario."""
        actions = []
        for action in self._get_available_actions(scenario_context or {}):
            actions.append({
                "action": action["name"],
                "label": self._format_action(action["name"], action["levels"][0]),
                "levels": [self._format_level(action["name"], level) for level in action["levels"]],
            })
        return actions

    def simulate_recommended_action_cashflow(self, forecast_analysis, action, level):
        """
        Apply the recommended action to the forecast burn path and simulate cashflow.
        """
        base_forecast = forecast_analysis.get("forecast_series", [])
        current_cash = forecast_analysis.get("current_cash", 0)

        adjusted_forecast = self._apply_action_to_forecast_series(base_forecast, action, level)
        projected_ending_cash = current_cash - sum(adjusted_forecast)

        return {
            "action": action,
            "level": level,
            "level_display": self._format_level(action, level),
            "forecast_values": [round(value, 2) for value in adjusted_forecast[:30]],
            "average_daily_burn": round(sum(adjusted_forecast) / len(adjusted_forecast), 2) if adjusted_forecast else 0,
            "projected_ending_cash": round(projected_ending_cash, 2),
            "monte_carlo": monte_carlo_cashflow(adjusted_forecast, current_cash),
        }

    def _apply_action_to_forecast_series(self, forecast_series, action, level):
        """Translate a recommended action into a revised burn trajectory."""
        adjusted = list(forecast_series)
        if not adjusted:
            return adjusted

        if action == "cut_marketing":
            reduction = 0.08 + (0.35 * level)
            return [max(5000, burn * (1 - reduction)) for burn in adjusted]

        if action == "reduce_discretionary":
            reduction = 0.05 + (0.22 * level)
            return [max(5000, burn * (1 - reduction)) for burn in adjusted]

        if action == "delay_vendor":
            relief_days = min(len(adjusted), max(1, int(level)))
            near_term_relief = 0.18 + (0.12 * min(1.0, level / 30))
            catch_up_penalty = 0.08 + (0.05 * min(1.0, level / 30))
            revised = []
            for index, burn in enumerate(adjusted):
                if index < relief_days:
                    revised.append(max(5000, burn * (1 - near_term_relief)))
                else:
                    revised.append(max(5000, burn * (1 + catch_up_penalty)))
            return revised

        if action == "optimize_cloud":
            reduction = 0.06 + (0.24 * level)
            return [max(5000, burn * (1 - reduction)) for burn in adjusted]

        if action == "freeze_hiring":
            reduction = 0.04 + (0.18 * level)
            return [max(5000, burn * (1 - reduction)) for burn in adjusted]

        if action == "rebalance_inventory":
            reduction = 0.05 + (0.2 * level)
            return [max(5000, burn * (1 - reduction)) for burn in adjusted]

        if action == "tighten_promotions":
            reduction = 0.04 + (0.16 * level)
            return [max(5000, burn * (1 - reduction)) for burn in adjusted]

        if action == "optimize_staffing_mix":
            reduction = 0.05 + (0.19 * level)
            return [max(5000, burn * (1 - reduction)) for burn in adjusted]

        if action == "tighten_procurement":
            reduction = 0.04 + (0.15 * level)
            return [max(5000, burn * (1 - reduction)) for burn in adjusted]

        if action == "defer_capex":
            reduction = 0.07 + (0.22 * level)
            return [max(5000, burn * (1 - reduction)) for burn in adjusted]

        if action == "consolidate_vendors":
            reduction = 0.03 + (0.14 * level)
            return [max(5000, burn * (1 - reduction)) for burn in adjusted]

        return adjusted


if __name__ == "__main__":
    from data import generate_financial_data, get_budget_config
    from features import build_features
    from agents.spend_agent import SpendIntelligenceAgent
    from agents.forecast_agent import CashFlowForecastAgent

    df = generate_financial_data()
    budget_config = get_budget_config()
    features = build_features(df, budget_config)

    spend_agent = SpendIntelligenceAgent()
    forecast_agent = CashFlowForecastAgent(current_cash=150000)

    spend_analysis = spend_agent.analyze(features, budget_config)
    forecast_analysis = forecast_agent.forecast(features)

    agent = DecisionAgent()
    decision = agent.make_decision(spend_analysis, forecast_analysis, features, budget_config)

    print("Decision Analysis:")
    print(f"  Best Action: {decision['best_action']}")
    print(f"  Level: {decision['level']}")
    print(f"  Confidence: {decision['confidence']:.2f}")
    print("  Comparisons:")
    for comp in decision["comparisons"]:
        print(
            f"    {comp['action']} @ {comp['level']}: "
            f"score={comp['score']:.3f}, risk={comp['risk_after']:.2f}"
        )
