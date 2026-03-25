"""
Cashflow Forecast Agent
Forecasts liquidity and identifies risk windows.
"""
import numpy as np
from inference import forecast_cashflow, calculate_risk_score, monte_carlo_cashflow


class CashFlowForecastAgent:
    """Forecast cashflow and identify liquidity risks."""
    
    def __init__(self, current_cash=100000, name="CashFlowForecastAgent"):
        self.name = name
        self.current_cash = current_cash
    
    def forecast(self, features, days_ahead=30, assumptions=None):
        """
        Forecast cashflow and identify risks.
        
        Args:
            features: Features dict from feature engineering
            days_ahead: Number of days to forecast
            
        Returns:
            Dict with forecast and risk analysis
        """
        assumptions = assumptions or {}
        scenario_context = features.get('scenario_context', {})
        burn_shock = float(assumptions.get('burn_shock_pct', 0))
        collections_delay = int(assumptions.get('collections_delay_days', 0))
        monte_carlo_sims = int(assumptions.get('monte_carlo_sims', 250))
        revenue_outlook = float(assumptions.get('revenue_outlook_pct', 0))
        hiring_growth = float(assumptions.get('hiring_growth_pct', 0))
        working_capital_efficiency = float(assumptions.get('working_capital_efficiency', 0))
        capital_efficiency_score = float(assumptions.get('capital_efficiency_score', 50))
        company_age_years = float(scenario_context.get('company_age_years', assumptions.get('company_age_years', 5)))

        # Get forecast
        forecast_data = forecast_cashflow(features, days_ahead=days_ahead)
        forecast_data = self._apply_liquidity_posture(forecast_data)
        arima_forecast_data = self._apply_liquidity_posture(
            forecast_cashflow(features, days_ahead=days_ahead, method='arima')
        )
        forecast_data = self._apply_advanced_assumptions(
            forecast_data,
            burn_shock,
            collections_delay,
            revenue_outlook,
            hiring_growth,
            working_capital_efficiency,
        )
        arima_forecast_data = self._apply_advanced_assumptions(
            arima_forecast_data,
            burn_shock,
            collections_delay,
            revenue_outlook,
            hiring_growth,
            working_capital_efficiency,
        )
        forecast_data = self._apply_capital_context(forecast_data, scenario_context)
        arima_forecast_data = self._apply_capital_context(arima_forecast_data, scenario_context)
        forecast_data = self._apply_state_of_business(forecast_data, scenario_context)
        arima_forecast_data = self._apply_state_of_business(arima_forecast_data, scenario_context)
        forecast_data = self._apply_age_and_capital_efficiency(forecast_data, company_age_years, capital_efficiency_score)
        arima_forecast_data = self._apply_age_and_capital_efficiency(arima_forecast_data, company_age_years, capital_efficiency_score)
        
        days_to_risk = self._days_until_risk(forecast_data['forecast_series'])
        projected_ending_cash = self.current_cash - sum(forecast_data['forecast_series'])
        liquidity_gap = self.current_cash - forecast_data['min_cash']
        risk_score = calculate_risk_score(
            forecast_data['min_cash'],
            self.current_cash,
            days_to_risk=days_to_risk,
            forecast_horizon_days=days_ahead,
        )

        if risk_score > 0.75:
            risk_level = 'critical'
        elif risk_score > 0.5:
            risk_level = 'high'
        elif risk_score > 0.25:
            risk_level = 'medium'
        else:
            risk_level = 'low'

        monte_carlo = monte_carlo_cashflow(
            forecast_data['forecast_series'],
            self.current_cash,
            n_simulations=monte_carlo_sims,
        )
        sensitivity_analysis = self._build_sensitivity_analysis(forecast_data['forecast_series'])
        driver_sensitivity = self._build_driver_sensitivity(
            forecast_data,
            burn_shock,
            collections_delay,
            revenue_outlook,
            hiring_growth,
            working_capital_efficiency,
            capital_efficiency_score,
            company_age_years,
        )
        stress_testing = self._build_stress_tests(arima_forecast_data, monte_carlo_sims)
        capital_efficiency = self._calculate_capital_efficiency(
            forecast_data,
            revenue_outlook,
            working_capital_efficiency,
            capital_efficiency_score,
            company_age_years,
        )
        peer_benchmark = self._build_peer_benchmark(
            features,
            forecast_data,
            monte_carlo_sims,
            monte_carlo,
        )
        reason = self._build_reason(
            risk_level,
            days_to_risk,
            forecast_data,
            self.current_cash / forecast_data['min_cash'] if forecast_data['min_cash'] > 0 else float('inf'),
            monte_carlo,
        )
        
        return {
            'risk_window_days': forecast_data['risk_window_days'],
            'min_cash': forecast_data['min_cash'],
            'risk_level': risk_level,
            'risk_score': risk_score,
            'forecast_series': forecast_data['forecast_series'],
            'average_daily_burn': forecast_data['average_daily_burn'],
            'current_cash': self.current_cash,
            'cash_ratio': self.current_cash / forecast_data['min_cash'] if forecast_data['min_cash'] > 0 else float('inf'),
            'projected_ending_cash': projected_ending_cash,
            'liquidity_gap': liquidity_gap,
            'burn_adjustment': forecast_data['burn_adjustment'],
            'burn_posture': forecast_data['burn_posture'],
            'forecast_method': forecast_data.get('method_used', 'regression'),
            'planning_assumptions': {
                'forecast_horizon_days': days_ahead,
                'burn_shock_pct': burn_shock,
                'collections_delay_days': collections_delay,
                'monte_carlo_sims': monte_carlo_sims,
                'revenue_outlook_pct': revenue_outlook,
                'hiring_growth_pct': hiring_growth,
                'working_capital_efficiency': working_capital_efficiency,
                'capital_efficiency_score': capital_efficiency_score,
                'company_age_years': company_age_years,
            },
            'sensitivity_analysis': sensitivity_analysis,
            'driver_sensitivity': driver_sensitivity,
            'stress_testing': stress_testing,
            'monte_carlo': monte_carlo,
            'peer_benchmark': peer_benchmark,
            'capital_efficiency': capital_efficiency,
            'reason': reason,
            'days_to_risk': days_to_risk,
        }

    def _apply_liquidity_posture(self, forecast_data):
        """
        Adjust the burn forecast based on liquidity posture.

        Lower cash forces a defensive operating plan; stronger cash allows a
        modest increase in discretionary spending and growth investment.
        """
        base_min_cash = forecast_data['min_cash']
        base_ratio = self.current_cash / base_min_cash if base_min_cash > 0 else float('inf')

        if base_ratio < 0.35:
            burn_multiplier = 0.84
            burn_posture = 'emergency cuts'
        elif base_ratio < 0.6:
            burn_multiplier = 0.9
            burn_posture = 'tight controls'
        elif base_ratio < 1.0:
            burn_multiplier = 0.96
            burn_posture = 'cautious spending'
        elif base_ratio > 2.0:
            burn_multiplier = 1.08
            burn_posture = 'growth investment'
        elif base_ratio > 1.5:
            burn_multiplier = 1.04
            burn_posture = 'measured expansion'
        else:
            burn_multiplier = 1.0
            burn_posture = 'steady state'

        adjusted_forecast = [daily_burn * burn_multiplier for daily_burn in forecast_data['forecast_series']]
        adjusted_array = adjusted_forecast[:7]

        return {
            'forecast_series': adjusted_forecast,
            'min_cash': (sum(adjusted_forecast) / len(adjusted_forecast) * 7) if adjusted_forecast else 0,
            'risk_window_days': adjusted_array.index(max(adjusted_array)) + 1 if adjusted_array else 1,
            'average_daily_burn': (sum(adjusted_forecast) / len(adjusted_forecast)) if adjusted_forecast else 0,
            'burn_adjustment': burn_multiplier - 1.0,
            'burn_posture': burn_posture,
            'method_used': forecast_data.get('method_used', 'regression'),
        }

    def _apply_advanced_assumptions(
        self,
        forecast_data,
        burn_shock,
        collections_delay,
        revenue_outlook,
        hiring_growth,
        working_capital_efficiency,
    ):
        """Apply user-controlled planning assumptions to the forecast path."""
        base_series = list(forecast_data['forecast_series'])
        if not base_series:
            return forecast_data

        adjusted_series = []
        for day_index, burn in enumerate(base_series, start=1):
            adjusted_burn = burn * (1 + burn_shock)
            adjusted_burn *= (1 + hiring_growth)
            adjusted_burn *= (1 - revenue_outlook)
            adjusted_burn *= (1 - working_capital_efficiency)
            if day_index <= collections_delay:
                adjusted_burn *= 1.12
            adjusted_series.append(max(5000, adjusted_burn))

        adjusted_array = adjusted_series[:7]
        burn_adjustment = (
            forecast_data.get('burn_adjustment', 0.0)
            + burn_shock
            + hiring_growth
            - revenue_outlook
            - working_capital_efficiency
            + (0.12 if collections_delay > 0 else 0.0)
        )

        return {
            'forecast_series': adjusted_series,
            'min_cash': (sum(adjusted_series) / len(adjusted_series) * 7) if adjusted_series else 0,
            'risk_window_days': adjusted_array.index(max(adjusted_array)) + 1 if adjusted_array else 1,
            'average_daily_burn': (sum(adjusted_series) / len(adjusted_series)) if adjusted_series else 0,
            'burn_adjustment': burn_adjustment,
            'burn_posture': forecast_data.get('burn_posture', 'steady state'),
            'method_used': forecast_data.get('method_used', 'regression'),
        }

    def _build_sensitivity_analysis(self, forecast_series):
        """Estimate how ending cash changes with burn-rate sensitivity."""
        scenarios = []
        for label, multiplier in [
            ('Burn -10%', 0.90),
            ('Base', 1.00),
            ('Burn +10%', 1.10),
            ('Burn +20%', 1.20),
        ]:
            adjusted = [burn * multiplier for burn in forecast_series]
            end_cash = self.current_cash - sum(adjusted)
            scenarios.append({
                'scenario': label,
                'burn_multiplier': multiplier,
                'end_cash': round(end_cash, 2),
            })
        return scenarios

    def _apply_capital_context(self, forecast_data, scenario_context):
        """Adjust burn path based on geography, company market cap, and funding stage."""
        country = scenario_context.get('country', 'united_states')
        funding_round = scenario_context.get('funding_round', 'series_a')
        company_market_capital = float(scenario_context.get('company_market_capital', 500))

        country_factor = {
            'united_states': 1.04,
            'india': 0.94,
            'singapore': 0.98,
            'united_kingdom': 1.0,
            'uae': 0.99,
            'germany': 0.97,
        }.get(country, 1.0)
        funding_factor = {
            'bootstrapped': 0.88,
            'seed': 0.94,
            'series_a': 1.0,
            'series_b': 1.05,
            'series_c': 1.1,
            'public': 1.14,
        }.get(funding_round, 1.0)
        market_cap_factor = 0.92 if company_market_capital < 250 else 1.0 if company_market_capital < 1000 else 1.06

        multiplier = country_factor * funding_factor * market_cap_factor
        adjusted_series = [max(5000, burn * multiplier) for burn in forecast_data['forecast_series']]
        adjusted_array = adjusted_series[:7]

        return {
            'forecast_series': adjusted_series,
            'min_cash': (sum(adjusted_series) / len(adjusted_series) * 7) if adjusted_series else 0,
            'risk_window_days': adjusted_array.index(max(adjusted_array)) + 1 if adjusted_array else 1,
            'average_daily_burn': (sum(adjusted_series) / len(adjusted_series)) if adjusted_series else 0,
            'burn_adjustment': forecast_data.get('burn_adjustment', 0.0) + (multiplier - 1.0),
            'burn_posture': forecast_data.get('burn_posture', 'steady state'),
            'method_used': forecast_data.get('method_used', 'regression'),
        }

    def _apply_state_of_business(self, forecast_data, scenario_context):
        """Adjust burn path for survival, profit, or growth mode."""
        state = scenario_context.get('state_of_business', 'profit')
        multiplier = {
            'survival': 0.88,
            'profit': 0.97,
            'growth': 1.12,
        }.get(state, 1.0)
        adjusted_series = [max(5000, burn * multiplier) for burn in forecast_data['forecast_series']]
        adjusted_array = adjusted_series[:7]
        state_posture = {
            'survival': 'survival mode',
            'profit': 'profit discipline',
            'growth': 'growth mode',
        }.get(state, state)
        return {
            'forecast_series': adjusted_series,
            'min_cash': (sum(adjusted_series) / len(adjusted_series) * 7) if adjusted_series else 0,
            'risk_window_days': adjusted_array.index(max(adjusted_array)) + 1 if adjusted_array else 1,
            'average_daily_burn': (sum(adjusted_series) / len(adjusted_series)) if adjusted_series else 0,
            'burn_adjustment': forecast_data.get('burn_adjustment', 0.0) + (multiplier - 1.0),
            'burn_posture': state_posture,
            'method_used': forecast_data.get('method_used', 'regression'),
        }

    def _build_driver_sensitivity(
        self,
        forecast_data,
        burn_shock,
        collections_delay,
        revenue_outlook,
        hiring_growth,
        working_capital_efficiency,
        capital_efficiency_score,
        company_age_years,
    ):
        """Build tornado-style driver sensitivity and simple elasticity coefficients."""
        baseline_end_cash = self.current_cash - sum(forecast_data['forecast_series'])
        scenarios = [
            ('Revenue Outlook', 0.05, {'revenue_outlook': revenue_outlook + 0.05}),
            ('Hiring Growth', 0.05, {'hiring_growth': hiring_growth + 0.05}),
            ('Working Capital Efficiency', 0.05, {'working_capital_efficiency': working_capital_efficiency + 0.05}),
            ('Burn Shock', 0.05, {'burn_shock': burn_shock + 0.05}),
            ('Collections Delay', 5.0, {'collections_delay': collections_delay + 5}),
            ('Capital Efficiency', 10.0, {'capital_efficiency_score': capital_efficiency_score + 10}),
            ('Company Age', 2.0, {'company_age_years': company_age_years + 2}),
        ]

        results = []
        for driver, shock_value, override in scenarios:
            stressed = self._apply_advanced_assumptions(
                {
                    'forecast_series': list(forecast_data['forecast_series']),
                    'burn_adjustment': forecast_data.get('burn_adjustment', 0.0),
                    'burn_posture': forecast_data.get('burn_posture', 'steady state'),
                    'method_used': forecast_data.get('method_used', 'regression'),
                },
                override.get('burn_shock', burn_shock),
                int(override.get('collections_delay', collections_delay)),
                override.get('revenue_outlook', revenue_outlook),
                override.get('hiring_growth', hiring_growth),
                override.get('working_capital_efficiency', working_capital_efficiency),
            )
            stressed = self._apply_age_and_capital_efficiency(
                stressed,
                override.get('company_age_years', company_age_years),
                override.get('capital_efficiency_score', capital_efficiency_score),
            )
            stressed_end_cash = self.current_cash - sum(stressed['forecast_series'])
            delta_end_cash = stressed_end_cash - baseline_end_cash

            if driver in {'Collections Delay', 'Capital Efficiency', 'Company Age'}:
                elasticity = delta_end_cash / shock_value if shock_value else 0.0
            else:
                driver_scale = abs(baseline_end_cash) if abs(baseline_end_cash) > 1 else 1.0
                elasticity = (delta_end_cash / driver_scale) / shock_value if shock_value else 0.0

            results.append({
                'driver': driver,
                'shock': '+5d' if driver == 'Collections Delay' else '+10 pts' if driver == 'Capital Efficiency' else '+2y' if driver == 'Company Age' else '+5%',
                'baseline_end_cash': round(baseline_end_cash, 2),
                'stressed_end_cash': round(stressed_end_cash, 2),
                'delta_end_cash': round(delta_end_cash, 2),
                'elasticity': round(elasticity, 3),
            })

        results.sort(key=lambda row: abs(row['delta_end_cash']), reverse=True)
        return results

    def _apply_age_and_capital_efficiency(self, forecast_data, company_age_years, capital_efficiency_score):
        """Adjust burn path using lifecycle maturity and capital efficiency."""
        age = min(max(float(company_age_years), 1.0), 50.0)
        efficiency = min(max(float(capital_efficiency_score), 0.0), 100.0)
        age_multiplier = 1.08 if age <= 3 else 1.02 if age <= 8 else 0.97 if age <= 15 else 0.93
        efficiency_multiplier = 1.14 - (efficiency / 100.0) * 0.28
        multiplier = age_multiplier * efficiency_multiplier

        adjusted_series = [max(5000, burn * multiplier) for burn in forecast_data['forecast_series']]
        adjusted_array = adjusted_series[:7]
        return {
            'forecast_series': adjusted_series,
            'min_cash': (sum(adjusted_series) / len(adjusted_series) * 7) if adjusted_series else 0,
            'risk_window_days': adjusted_array.index(max(adjusted_array)) + 1 if adjusted_array else 1,
            'average_daily_burn': (sum(adjusted_series) / len(adjusted_series)) if adjusted_series else 0,
            'burn_adjustment': forecast_data.get('burn_adjustment', 0.0) + (multiplier - 1.0),
            'burn_posture': forecast_data.get('burn_posture', 'steady state'),
            'method_used': forecast_data.get('method_used', 'regression'),
        }

    def _calculate_capital_efficiency(self, forecast_data, revenue_outlook, working_capital_efficiency, capital_efficiency_score, company_age_years):
        """Build a UI-friendly capital efficiency KPI block."""
        burn = max(forecast_data.get('average_daily_burn', 0.0), 1.0)
        efficiency_input = min(max(float(capital_efficiency_score), 0.0), 100.0) / 100.0
        age_modifier = 0.92 if company_age_years <= 3 else 1.0 if company_age_years <= 10 else 1.08
        efficiency_index = min(1.5, max(0.2, (0.55 + efficiency_input * 0.55 + revenue_outlook * 0.25 + working_capital_efficiency * 0.35) * age_modifier))
        burn_multiple = max(0.1, burn / max(self.current_cash, 1.0))
        status = 'strong' if efficiency_index >= 1.0 else 'moderate' if efficiency_index >= 0.75 else 'weak'
        return {
            'index': round(efficiency_index, 3),
            'burn_multiple': round(burn_multiple, 3),
            'status': status,
        }

    def _build_stress_tests(self, arima_forecast_data, monte_carlo_sims):
        """Build ARIMA-based stress cases for FP&A and treasury review."""
        arima_series = arima_forecast_data['forecast_series']
        stress_cases = [
            ('ARIMA Base', 1.00),
            ('ARIMA Stress +10%', 1.10),
            ('ARIMA Severe +20%', 1.20),
        ]
        results = []
        for name, multiplier in stress_cases:
            stressed_series = [burn * multiplier for burn in arima_series]
            monte_carlo = monte_carlo_cashflow(stressed_series, self.current_cash, n_simulations=monte_carlo_sims)
            results.append({
                'scenario': name,
                'forecast_method': arima_forecast_data.get('method_used', 'arima'),
                'avg_daily_burn': round(sum(stressed_series) / len(stressed_series), 2) if stressed_series else 0,
                'end_cash': round(self.current_cash - sum(stressed_series), 2),
                'days_to_risk': self._days_until_risk(stressed_series),
                'shortfall_probability': monte_carlo['breach_probability'],
            })
        return results

    def _build_peer_benchmark(self, features, forecast_data, monte_carlo_sims, monte_carlo):
        """Build a synthetic peer cohort for the same sector and business scale."""
        scenario_context = features.get('scenario_context', {})
        sector = scenario_context.get('sector', 'saas')
        business_scale = scenario_context.get('business_scale', 'mid_market')
        macro_environment = scenario_context.get('macro_environment', 'stable')
        state_of_business = scenario_context.get('state_of_business', 'profit')

        sector_burn_factor = {
            'saas': 0.97,
            'retail': 1.03,
            'healthcare': 1.01,
            'manufacturing': 1.02,
            'fintech': 0.96,
            'logistics': 1.04,
            'hospitality': 1.05,
            'education': 0.99,
        }.get(sector, 1.0)
        scale_burn_factor = {
            'small_business': 1.05,
            'startup': 1.03,
            'mid_market': 1.0,
            'enterprise': 0.98,
            'large_enterprise': 0.96,
        }.get(business_scale, 1.0)
        macro_burn_factor = {
            'stable': 1.0,
            'inflationary': 1.02,
            'recessionary': 0.99,
        }.get(macro_environment, 1.0)
        state_burn_factor = {
            'survival': 0.93,
            'profit': 0.99,
            'growth': 1.08,
        }.get(state_of_business, 1.0)

        sector_cash_buffer = {
            'saas': 1.02,
            'retail': 0.98,
            'healthcare': 1.03,
            'manufacturing': 1.0,
            'fintech': 1.06,
            'logistics': 0.99,
            'hospitality': 0.95,
            'education': 1.01,
        }.get(sector, 1.0)
        scale_cash_buffer = {
            'small_business': 0.92,
            'startup': 0.95,
            'mid_market': 1.0,
            'enterprise': 1.08,
            'large_enterprise': 1.15,
        }.get(business_scale, 1.0)

        peer_burn_multiplier = sector_burn_factor * scale_burn_factor * macro_burn_factor * state_burn_factor
        peer_starting_cash = self.current_cash * sector_cash_buffer * scale_cash_buffer
        peer_forecast_series = [max(5000, burn * peer_burn_multiplier) for burn in forecast_data['forecast_series']]
        peer_monte_carlo = monte_carlo_cashflow(
            peer_forecast_series,
            peer_starting_cash,
            n_simulations=max(150, monte_carlo_sims),
            seed=84,
        )

        company_median_end_cash = float(monte_carlo.get('median_end_cash', 0))
        peer_distribution = np.array([
            peer_monte_carlo.get('p10_end_cash', 0.0),
            peer_monte_carlo.get('median_end_cash', 0.0),
            peer_monte_carlo.get('p90_end_cash', 0.0),
        ], dtype=float)
        percentile_rank = float(np.mean(peer_distribution <= company_median_end_cash))
        relative_position = (
            'ahead of peers' if company_median_end_cash >= peer_monte_carlo.get('p90_end_cash', 0)
            else 'above peer median' if company_median_end_cash >= peer_monte_carlo.get('median_end_cash', 0)
            else 'below peer median' if company_median_end_cash >= peer_monte_carlo.get('p10_end_cash', 0)
            else 'lagging peers'
        )

        return {
            'label': f"Synthetic peer cohort: {sector.replace('_', ' ').title()} / {business_scale.replace('_', ' ').title()}",
            'starting_cash': round(peer_starting_cash, 2),
            'burn_multiplier': round(peer_burn_multiplier, 3),
            'relative_position': relative_position,
            'percentile_rank': round(percentile_rank, 2),
            'monte_carlo': peer_monte_carlo,
        }
    
    def _days_until_risk(self, forecast_series):
        """
        Calculate days until cumulative burn exhausts available cash.
        
        Args:
            forecast_series: List of daily burn rates
            
        Returns:
            Days until risk
        """
        cumulative_burn = 0
        
        for i, daily_burn in enumerate(forecast_series):
            cumulative_burn += daily_burn
            if cumulative_burn >= self.current_cash:
                return i + 1
        
        return len(forecast_series)
    
    def _build_reason(self, risk_level, days_to_risk, forecast_data, cash_ratio, monte_carlo):
        """Build human-readable risk explanation."""
        breach_probability = int(monte_carlo['breach_probability'] * 100)
        warning_horizon_days = int(monte_carlo.get('warning_horizon_days', 14))
        if risk_level == 'critical':
            return (
                f"Critical cash risk: Under a {forecast_data['burn_posture']} posture, cash is projected "
                f"to last about {days_to_risk} days, with a {breach_probability}% Monte Carlo shortfall probability "
                f"within {warning_horizon_days} days."
            )
        elif risk_level == 'high':
            return (
                f"High cash risk: With a {forecast_data['burn_posture']} plan and burn averaging "
                f"${forecast_data['average_daily_burn']:,.0f}, cash will be constrained in {days_to_risk} days. "
                f"Monte Carlo shortfall probability within {warning_horizon_days} days is {breach_probability}%."
            )
        elif risk_level == 'medium':
            return (
                f"Medium cash risk: Operating under a {forecast_data['burn_posture']} plan, current cash covers "
                f"{cash_ratio:.2f}x projected needs, with {breach_probability}% simulated downside risk "
                f"within {warning_horizon_days} days."
            )
        return (
            f"Low cash risk: Liquidity supports a {forecast_data['burn_posture']} plan for at least "
            f"{days_to_risk} days, with Monte Carlo downside risk contained to {breach_probability}% "
            f"within {warning_horizon_days} days."
        )
    
    def get_context(self):
        """Get agent context for orchestrator."""
        return {
            'name': self.name,
            'role': 'Cashflow Forecasting',
            'responsibility': 'Forecast liquidity and identify cash risk windows',
        }


if __name__ == '__main__':
    from data import generate_financial_data, get_budget_config
    from features import build_features
    
    df = generate_financial_data()
    budget_config = get_budget_config()
    features = build_features(df, budget_config)
    
    agent = CashFlowForecastAgent(current_cash=150000)
    result = agent.forecast(features)
    
    print("Cashflow Forecast Analysis:")
    print(f"  Risk Level: {result['risk_level']}")
    print(f"  Risk Score: {result['risk_score']:.2f}")
    print(f"  Min Cash Needed: ${result['min_cash']:,.2f}")
    print(f"  Days to Risk: {result['days_to_risk']}")
    print(f"  Cash Ratio: {result['cash_ratio']:.2f}x")
