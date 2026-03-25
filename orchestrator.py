"""
Orchestrator
Main system controller coordinating all agents.
"""
import uuid
from datetime import datetime
from data import get_transaction_data, get_budget_config, get_upcoming_payments
from features import build_features, get_feature_summary
from agents.spend_agent import SpendIntelligenceAgent
from agents.forecast_agent import CashFlowForecastAgent
from agents.decision_agent import DecisionAgent
from agents.narrative_agent import NarrativeAgent
from memory import memory
from evaluation import evaluator


class CFOOrchestrator:
    """
    Main orchestrator for the AI-Native CFO Operating System.
    Coordinates multi-agent decision-making pipeline.
    """
    
    def __init__(
        self,
        current_cash=700000,
        sector='saas',
        business_scale='mid_market',
        macro_environment='stable',
        country='united_states',
        company_market_capital=500,
        funding_round='series_a',
        state_of_business='profit',
        company_age_years=5,
        close_pressure='medium',
        planning_assumptions=None,
        automation_maturity='medium',
        data_source='synthetic',
        zaggle_export_path=None,
        country_market_capital=None,
    ):
        if country_market_capital is not None:
            company_market_capital = country_market_capital
        self.current_cash = current_cash
        self.sector = sector
        self.business_scale = business_scale
        self.macro_environment = macro_environment
        self.country = country
        self.company_market_capital = company_market_capital
        self.funding_round = funding_round
        self.state_of_business = state_of_business
        self.company_age_years = company_age_years
        self.close_pressure = close_pressure
        self.planning_assumptions = planning_assumptions or {}
        self.automation_maturity = automation_maturity
        self.data_source = data_source
        self.zaggle_export_path = zaggle_export_path
        self.spend_agent = SpendIntelligenceAgent()
        self.forecast_agent = CashFlowForecastAgent(current_cash=current_cash)
        self.decision_agent = DecisionAgent()
        self.narrative_agent = NarrativeAgent(use_openai=False)
        self.session_id = str(uuid.uuid4())[:8]
        self.budget_config = get_budget_config()
    
    def run_analysis(self, days=90):
        """
        Execute full CFO analysis pipeline.
        
        Args:
            days: Days of historical data to generate
            
        Returns:
            Dict with complete analysis results
        """
        # Step 1: Generate data
        df, source_metadata = get_transaction_data(
            source=self.data_source,
            days=days,
            sector=self.sector,
            business_scale=self.business_scale,
            macro_environment=self.macro_environment,
            country=self.country,
            company_market_capital=self.company_market_capital,
            funding_round=self.funding_round,
            state_of_business=self.state_of_business,
            company_age_years=self.company_age_years,
            capital_efficiency_score=self.planning_assumptions.get('capital_efficiency_score', 50),
            zaggle_export_path=self.zaggle_export_path,
        )
        upcoming_payments = get_upcoming_payments(
            sector=self.sector,
            business_scale=self.business_scale,
            macro_environment=self.macro_environment,
            country=self.country,
            company_market_capital=self.company_market_capital,
            funding_round=self.funding_round,
            state_of_business=self.state_of_business,
            company_age_years=self.company_age_years,
            capital_efficiency_score=self.planning_assumptions.get('capital_efficiency_score', 50),
            close_pressure=self.close_pressure,
        )
        
        # Step 2: Build features
        features = build_features(df, self.budget_config)
        features['scenario_context'] = {
            'sector': self.sector,
            'business_scale': self.business_scale,
            'macro_environment': self.macro_environment,
            'country': self.country,
            'company_market_capital': self.company_market_capital,
            'funding_round': self.funding_round,
            'state_of_business': self.state_of_business,
            'company_age_years': self.company_age_years,
            'capital_efficiency_score': self.planning_assumptions.get('capital_efficiency_score', 50),
            'close_pressure': self.close_pressure,
            'planning_assumptions': self.planning_assumptions,
            'automation_maturity': self.automation_maturity,
            'data_source': self.data_source,
        }
        feature_summary = get_feature_summary(features)
        
        # Step 3: Run Spend Agent
        spend_analysis = self.spend_agent.analyze(features, self.budget_config)
        
        # Record in memory if anomaly detected
        if spend_analysis['severity'] != 'low':
            memory.record_anomaly(
                category=spend_analysis['category'],
                severity=spend_analysis['severity'],
                percent_change=spend_analysis['percent_change'],
                reason=spend_analysis['reason']
            )
        
        # Step 4: Run Forecast Agent
        forecast_analysis = self.forecast_agent.forecast(
            features,
            days_ahead=int(self.planning_assumptions.get('forecast_horizon_days', 30)),
            assumptions=self.planning_assumptions,
        )
        
        # Step 5: Run Decision Agent (critical - includes simulation)
        decision_analysis = self.decision_agent.make_decision(
            spend_analysis,
            forecast_analysis,
            features,
            self.budget_config
        )
        available_actions = self.decision_agent.get_available_actions(features.get('scenario_context'))
        action_simulation = self.decision_agent.simulate_recommended_action_cashflow(
            forecast_analysis,
            decision_analysis['best_action'],
            decision_analysis.get('level', 0),
        )
        fpa_analysis = self._build_fpa_analysis(
            features,
            forecast_analysis,
            decision_analysis,
            action_simulation,
        )
        compliance_analysis = self._build_compliance_analysis(df, spend_analysis, upcoming_payments)
        
        # Record decision
        memory.record_decision(
            action=decision_analysis['best_action'],
            risk_score=forecast_analysis['risk_score'],
            confidence=decision_analysis['confidence'],
            context=f"Spend: {spend_analysis['category']}, Forecast risk: {forecast_analysis['risk_level']}"
        )
        
        # Step 6: Run Narrative Agent
        narrative = self.narrative_agent.generate_briefing(
            spend_analysis,
            forecast_analysis,
            decision_analysis
        )
        
        # Step 7: Compile results
        result = {
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'current_cash': self.current_cash,
            'sector': self.sector,
            'business_scale': self.business_scale,
            'macro_environment': self.macro_environment,
            'country': self.country,
            'company_market_capital': self.company_market_capital,
            'funding_round': self.funding_round,
            'state_of_business': self.state_of_business,
            'company_age_years': self.company_age_years,
            'capital_efficiency_score': self.planning_assumptions.get('capital_efficiency_score', 50),
            'close_pressure': self.close_pressure,
            'automation_maturity': self.automation_maturity,
            'data_source': source_metadata.get('data_source', self.data_source),
            'data_source_status': source_metadata.get('data_source_status', 'connected'),
            'data_source_message': source_metadata.get('data_source_message', ''),
            'zaggle_export_path': self.zaggle_export_path,
            'planning_assumptions': self.planning_assumptions,
            'analysis_horizon': days,
            
            # Raw data
            'transaction_count': len(df),
            'date_range': {
                'start': df['date'].min().isoformat() if len(df) > 0 else None,
                'end': df['date'].max().isoformat() if len(df) > 0 else None,
            },
            
            # Feature summary
            'feature_summary': feature_summary,
            'mtd_spend_by_category': spend_analysis.get('category', None),
            
            # Reports from each agent
            'spend_intelligence': {
                'issue': spend_analysis['issue'],
                'category': spend_analysis['category'],
                'percent_change': spend_analysis['percent_change'],
                'severity': spend_analysis['severity'],
                'confidence': spend_analysis['confidence'],
                'anomaly_scores': spend_analysis.get('anomaly_scores', {}),
                'budget_consumption_rate': spend_analysis.get('budget_consumption_rate', {}),
                'vendor_concentration': spend_analysis.get('vendor_concentration', {}),
                'headline_budget_consumption': spend_analysis.get('headline_budget_consumption', 0),
                'headline_vendor_hhi': spend_analysis.get('headline_vendor_hhi', 0),
                'headline_top_vendor': spend_analysis.get('headline_top_vendor', 'n/a'),
                'headline_top_vendor_share': spend_analysis.get('headline_top_vendor_share', 0),
            },
            
            'cashflow_forecast': {
                'risk_level': forecast_analysis['risk_level'],
                'risk_score': forecast_analysis['risk_score'],
                'min_cash': forecast_analysis['min_cash'],
                'days_to_risk': forecast_analysis['days_to_risk'],
                'average_daily_burn': forecast_analysis['average_daily_burn'],
                'cash_ratio': forecast_analysis['cash_ratio'],
                'projected_ending_cash': forecast_analysis['projected_ending_cash'],
                'liquidity_gap': forecast_analysis['liquidity_gap'],
                'burn_adjustment': forecast_analysis['burn_adjustment'],
                'burn_posture': forecast_analysis['burn_posture'],
                'forecast_method': forecast_analysis['forecast_method'],
                'sensitivity_analysis': forecast_analysis['sensitivity_analysis'],
                'driver_sensitivity': forecast_analysis.get('driver_sensitivity', []),
                'stress_testing': forecast_analysis['stress_testing'],
                'monte_carlo': forecast_analysis['monte_carlo'],
                'peer_benchmark': forecast_analysis.get('peer_benchmark', {}),
                'forecast_values': forecast_analysis['forecast_series'][:30],  # Next 30 days
            },
            
            'decision_analysis': {
                'best_action': decision_analysis['best_action'],
                'level': decision_analysis.get('level'),
                'level_display': decision_analysis.get('level_display'),
                'confidence': decision_analysis['confidence'],
                'comparisons': decision_analysis['comparisons'],
                'reasoning': decision_analysis['reasoning'],
                'available_actions': available_actions,
                'recommended_action_simulation': action_simulation,
            },
            
            'executive_briefing': {
                'narrative': narrative['narrative'],
                'source': narrative['source'],
            },

            'fpa_analysis': fpa_analysis,
            'compliance_analysis': compliance_analysis,
            
            # System metadata
            'memory_snapshot': {
                'anomalies_24h': memory.get_anomaly_count(24),
                'recent_anomalies': memory.get_last_anomalies(3),
            },
        }
        
        return result

    def _build_compliance_analysis(self, df, spend_analysis, upcoming_payments):
        """
        Build a lightweight compliance and close view using transaction anomalies,
        reconciliation coverage, and upcoming payment exceptions.
        """
        high_value_threshold = float(df['amount'].quantile(0.95)) if len(df) > 0 else 0
        recent_cutoff = df['date'].max() - (df['date'].max() - df['date'].min()) * 0.15 if len(df) > 0 else None
        liquidity_pressure = 1.0 if self.current_cash < 100000 else 0.75 if self.current_cash < 200000 else 0.45
        close_pressure_factor = {'low': 0.8, 'medium': 1.0, 'high': 1.2, 'quarter_end': 1.45}.get(self.close_pressure, 1.0)
        automation_factor = {'low': 1.15, 'medium': 1.0, 'high': 0.82}.get(self.automation_maturity, 1.0)
        macro_escalation = {'stable': 1.0, 'inflationary': 1.15, 'recessionary': 1.1}.get(self.macro_environment, 1.0)
        country_factor = {'united_states': 0.98, 'india': 1.04, 'singapore': 0.96, 'united_kingdom': 1.0, 'uae': 1.01, 'germany': 0.99}.get(self.country, 1.0)
        funding_factor = {'bootstrapped': 1.12, 'seed': 1.08, 'series_a': 1.0, 'series_b': 0.97, 'series_c': 0.94, 'public': 0.9}.get(self.funding_round, 1.0)
        state_factor = {'survival': 1.08, 'profit': 0.96, 'growth': 1.03}.get(self.state_of_business, 1.0)
        market_cap_factor = 1.1 if self.company_market_capital < 250 else 1.0 if self.company_market_capital < 1000 else 0.92
        sector_escalation = {
            'saas': 0.95,
            'retail': 1.15,
            'healthcare': 1.1,
            'manufacturing': 1.2,
            'fintech': 1.05,
            'logistics': 1.18,
            'hospitality': 1.12,
            'education': 1.0,
        }.get(self.sector, 1.0)
        close_risk_index = (
            liquidity_pressure
            * macro_escalation
            * country_factor
            * funding_factor
            * state_factor
            * market_cap_factor
            * sector_escalation
            * close_pressure_factor
            * automation_factor
        )

        exception_rows = []
        if len(df) > 0:
            flagged_df = df[
                (df['amount'] >= high_value_threshold)
                | (df['category'] == spend_analysis.get('category'))
                | ((recent_cutoff is not None) & (df['date'] >= recent_cutoff))
            ].sort_values('amount', ascending=False)
            sampled = flagged_df.head(8)
            for _, row in sampled.iterrows():
                tags = []
                if row['amount'] >= high_value_threshold:
                    tags.append('high value')
                if spend_analysis.get('category') == row['category']:
                    tags.append('anomaly category')
                if recent_cutoff is not None and row['date'] >= recent_cutoff:
                    tags.append('recent activity')

                exception_rows.append({
                    'date': row['date'].date().isoformat(),
                    'vendor': row['vendor'],
                    'category': row['category'],
                    'amount': round(float(row['amount']), 2),
                    'flags': ", ".join(tags) if tags else 'review',
                })

        reconciliation_rows = []
        matched_count = 0
        open_count = 0
        overdue_count = 0
        match_threshold = 7000 * (1.1 if self.current_cash > 250000 else 1.0) * (1.0 / close_pressure_factor) * (1.25 if self.automation_maturity == 'high' else 1.0)
        review_threshold = 16000 / max(0.8, close_risk_index)
        for payment in upcoming_payments:
            if payment['amount'] <= match_threshold and close_risk_index < 1.0:
                status = 'matched'
                matched_count += 1
            elif payment['amount'] <= review_threshold:
                status = 'review'
                open_count += 1
            else:
                status = 'escalate'
                overdue_count += 1

            reconciliation_rows.append({
                'date': payment['date'].isoformat(),
                'vendor': payment['vendor'],
                'category': payment['category'],
                'amount': round(float(payment['amount']), 2),
                'status': status,
            })

        total_items = len(reconciliation_rows)
        auto_match_rate = matched_count / total_items if total_items else 0
        close_risk_score = overdue_count + (open_count * 0.5) + (close_risk_index - 1.0)
        close_risk = 'high' if close_risk_score >= 2.5 else 'medium' if close_risk_score >= 1.2 else 'low'

        return {
            'headline': (
                f"Compliance and close view: {matched_count} items auto-matched, "
                f"{open_count} require review, and {overdue_count} need escalation."
            ),
            'kpis': {
                'auto_match_rate': round(auto_match_rate, 3),
                'review_queue': open_count,
                'escalations': overdue_count,
                'close_risk': close_risk,
                'flagged_transactions': int(len(flagged_df)) if len(df) > 0 else 0,
                'close_pressure': self.close_pressure,
                'automation_maturity': self.automation_maturity,
            },
            'exceptions': exception_rows,
            'reconciliations': reconciliation_rows,
        }

    def _build_fpa_analysis(self, features, forecast_analysis, decision_analysis, action_simulation):
        """
        Build an FP&A layer with variance analysis, planning KPIs, and scenarios.
        """
        variance_table = []
        total_budget = 0
        total_actual = 0

        for category, budget in self.budget_config.items():
            actual = float(features['mtd_spend'].get(category, 0))
            variance = actual - budget
            variance_pct = (variance / budget) if budget else 0
            total_budget += budget
            total_actual += actual

            if variance_pct > 0.1:
                status = 'over budget'
            elif variance_pct < -0.1:
                status = 'under budget'
            else:
                status = 'on plan'

            variance_table.append({
                'category': category,
                'budget': round(budget, 2),
                'actual': round(actual, 2),
                'variance': round(variance, 2),
                'variance_pct': round(variance_pct, 3),
                'status': status,
            })

        variance_table.sort(key=lambda row: abs(row['variance']), reverse=True)
        recommended_mc = action_simulation.get('monte_carlo', {})
        baseline_mc = forecast_analysis.get('monte_carlo', {})

        scenarios = [
            {
                'name': 'Base Plan',
                'description': 'Continue with the current operating posture.',
                'avg_daily_burn': round(forecast_analysis['average_daily_burn'], 2),
                'end_cash': round(forecast_analysis['projected_ending_cash'], 2),
                'shortfall_probability': baseline_mc.get('breach_probability', 0),
            },
            {
                'name': 'Recommended Action',
                'description': f"{decision_analysis['best_action'].replace('_', ' ').title()} at {decision_analysis.get('level_display', decision_analysis.get('level'))}.",
                'avg_daily_burn': round(action_simulation.get('average_daily_burn', 0), 2),
                'end_cash': round(action_simulation.get('projected_ending_cash', 0), 2),
                'shortfall_probability': recommended_mc.get('breach_probability', 0),
            },
            {
                'name': 'Stress Case',
                'description': 'Burn increases by 12% and collections soften.',
                'avg_daily_burn': round(forecast_analysis['average_daily_burn'] * 1.12, 2),
                'end_cash': round(self.current_cash - (sum(forecast_analysis['forecast_series']) * 1.12), 2),
                'shortfall_probability': min(1.0, round(baseline_mc.get('breach_probability', 0) + 0.12, 3)),
            },
        ]

        total_variance = total_actual - total_budget
        plan_attainment = (total_actual / total_budget) if total_budget else 0
        current_burn = float(features['burn_rate'][-1]) if len(features['burn_rate']) > 0 else 0
        prior_burn = float(features['burn_rate'][-8]) if len(features['burn_rate']) > 7 else current_burn
        burn_change_pct = ((current_burn - prior_burn) / prior_burn) if prior_burn else 0
        top_variance_driver = variance_table[0]['category'] if variance_table else None
        variance_direction = 'above' if total_variance > 0 else 'below'
        capital_efficiency = forecast_analysis.get('capital_efficiency', {})
        company_age_years = self.company_age_years
        lifecycle_stage = (
            'early' if company_age_years <= 3
            else 'growth' if company_age_years <= 8
            else 'scale' if company_age_years <= 15
            else 'mature'
        )
        state_of_business = self.state_of_business
        headline = (
            f"FP&A view: month-to-date spend is {variance_direction} plan by "
            f"${abs(total_variance):,.0f}. Recommended action improves projected end cash by "
            f"${action_simulation.get('projected_ending_cash', 0) - forecast_analysis['projected_ending_cash']:,.0f}."
        )
        planning_narration = (
            f"Planning narration: spend is {variance_direction} plan, with {top_variance_driver or 'no clear'} as "
            f"the main variance driver. Burn is {'up' if burn_change_pct > 0 else 'down'} "
            f"{abs(burn_change_pct):.0%} versus the prior weekly run-rate, and the recommended action "
            f"supports a projected 30-day cash improvement of "
            f"${action_simulation.get('projected_ending_cash', 0) - forecast_analysis['projected_ending_cash']:,.0f}. "
            f"Capital efficiency is currently {capital_efficiency.get('status', 'moderate')} with a "
            f"{lifecycle_stage} company profile in a {state_of_business} operating state."
        )

        return {
            'headline': headline,
            'variance_table': variance_table,
            'top_variance_driver': top_variance_driver,
            'planning_narration': planning_narration,
            'kpis': {
                'total_budget': round(total_budget, 2),
                'total_actual': round(total_actual, 2),
                'total_variance': round(total_variance, 2),
                'plan_attainment': round(plan_attainment, 3),
                'runway_days': forecast_analysis['days_to_risk'],
                'forecast_burn': round(forecast_analysis['average_daily_burn'], 2),
                'current_burn': round(current_burn, 2),
                'burn_change_pct': round(burn_change_pct, 3),
                'budget_utilization': round((total_actual / total_budget), 3) if total_budget else 0,
                'capital_efficiency_index': capital_efficiency.get('index', 0),
                'capital_efficiency_status': capital_efficiency.get('status', 'moderate'),
                'capital_burn_multiple': capital_efficiency.get('burn_multiple', 0),
                'company_age_years': company_age_years,
                'lifecycle_stage': lifecycle_stage,
                'state_of_business': state_of_business,
                'recommended_end_cash_delta': round(
                    action_simulation.get('projected_ending_cash', 0) - forecast_analysis['projected_ending_cash'],
                    2,
                ),
            },
            'scenarios': scenarios,
            'sensitivity_analysis': forecast_analysis.get('sensitivity_analysis', []),
            'driver_sensitivity': forecast_analysis.get('driver_sensitivity', []),
            'stress_testing': forecast_analysis.get('stress_testing', []),
            'platform_features': [
                'Revenue outlook planning',
                'Hiring plan sensitivity',
                'Working capital optimization',
                'Finance automation maturity',
                'Budget consumption monitoring',
                'Vendor concentration analysis',
            ],
        }
    
    def get_system_status(self):
        """Get overall system status and health."""
        last_decision = memory.get_last_decision()
        pattern = memory.get_pattern_summary()
        
        return {
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'agents': {
                'spend_intelligence': self.spend_agent.get_context(),
                'cashflow_forecast': self.forecast_agent.get_context(),
                'decision_making': self.decision_agent.get_context(),
                'narrative': self.narrative_agent.get_context(),
            },
            'last_decision': last_decision,
            'pattern_analysis': pattern,
            'memory_state': {
                'anomaly_records': len(memory.anomalies),
                'decision_records': len(memory.decisions),
            },
        }


def main():
    """Demo run of the orchestrator."""
    print("=" * 60)
    print("AI-NATIVE CFO OPERATING SYSTEM")
    print("=" * 60)
    
    orchestrator = CFOOrchestrator(current_cash=700000)
    
    print("\n[ORCHESTRATOR] Starting multi-agent analysis pipeline...")
    result = orchestrator.run_analysis(days=90)
    
    print("\n" + "=" * 60)
    print("ANALYSIS RESULTS")
    print("=" * 60)
    
    print(f"\n[SPEND INTELLIGENCE]")
    print(f"  Issue: {result['spend_intelligence']['issue']}")
    print(f"  Category: {result['spend_intelligence']['category']}")
    print(f"  Change: {result['spend_intelligence']['percent_change']:.1f}%")
    print(f"  Severity: {result['spend_intelligence']['severity']}")
    
    print(f"\n[CASHFLOW FORECAST]")
    print(f"  Risk Level: {result['cashflow_forecast']['risk_level']}")
    print(f"  Risk Score: {result['cashflow_forecast']['risk_score']:.2f}")
    print(f"  Days to Risk: {result['cashflow_forecast']['days_to_risk']}")
    print(f"  Min Cash: ${result['cashflow_forecast']['min_cash']:,.0f}")
    
    print(f"\n[DECISION ANALYSIS]")
    print(f"  Best Action: {result['decision_analysis']['best_action']}")
    print(f"  Confidence: {result['decision_analysis']['confidence']:.0%}")
    
    print(f"\n[EXECUTIVE BRIEFING]")
    print(result['executive_briefing']['narrative'])
    
    print("\n" + "=" * 60)
    print("System status available via orchestrator.get_system_status()")
    print("=" * 60)
    
    return result


if __name__ == '__main__':
    main()
