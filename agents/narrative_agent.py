"""
Narrative Agent
Generate CFO-level executive briefing.
"""
import os


class NarrativeAgent:
    """Generate executive-level narrative explanations."""
    
    def __init__(self, use_openai=False, name="NarrativeAgent"):
        self.name = name
        self.use_openai = use_openai and os.getenv('OPENAI_API_KEY')
        
        if self.use_openai:
            try:
                from openai import OpenAI
                self.client = OpenAI()
            except Exception:
                self.use_openai = False
    
    def generate_briefing(self, spend_analysis, forecast_analysis, decision_analysis):
        """
        Generate executive CFO briefing.
        
        Args:
            spend_analysis: Output from SpendIntelligenceAgent
            forecast_analysis: Output from CashFlowForecastAgent
            decision_analysis: Output from DecisionAgent
            
        Returns:
            Dict with narrative and recommendations
        """
        if self.use_openai:
            return self._generate_with_llm(spend_analysis, forecast_analysis, decision_analysis)
        else:
            return self._generate_template_briefing(spend_analysis, forecast_analysis, decision_analysis)
    
    def _generate_with_llm(self, spend_analysis, forecast_analysis, decision_analysis):
        """Generate briefing using OpenAI API."""
        try:
            prompt = self._build_llm_prompt(spend_analysis, forecast_analysis, decision_analysis)
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial expert CFO assistant. Provide clear, concise executive briefings without technical jargon."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=500,
            )
            
            narrative = response.choices[0].message.content
            source = "LLM"
        
        except Exception as e:
            print(f"LLM generation failed: {e}. Falling back to template.")
            return self._generate_template_briefing(spend_analysis, forecast_analysis, decision_analysis)
        
        return {
            'narrative': narrative,
            'source': source,
            'tone': 'executive',
        }
    
    def _build_llm_prompt(self, spend_analysis, forecast_analysis, decision_analysis):
        """Build prompt for LLM."""
        return f"""
Based on today's financial analysis, provide a brief CFO executive briefing:

SPENDING ANALYSIS:
- Issue: {spend_analysis['issue']}
- Severity: {spend_analysis['severity']}
- Category: {spend_analysis['category']}
- Change: {spend_analysis['percent_change']:.1f}%

CASHFLOW FORECAST:
- Risk Level: {forecast_analysis['risk_level']}
- Days to Risk: {forecast_analysis['days_to_risk']}
- Current Cash: ${forecast_analysis['current_cash']:,.0f}
- Min Needed: ${forecast_analysis['min_cash']:,.0f}

RECOMMENDATION:
- Action: {decision_analysis['best_action']}
- Decision Margin: {decision_analysis['confidence']:.0%}

Write a 3-4 sentence executive summary suitable for a CFO review. Focus on:
1. Current financial status
2. Key risk
3. Recommended action and why
4. Expected impact

Keep it professional, clear, and avoid technical jargon.
"""
    
    def _generate_template_briefing(self, spend_analysis, forecast_analysis, decision_analysis):
        """Generate briefing from template."""
        severity_emoji = {
            'critical': '🚨',
            'high': '⚠️',
            'medium': '📊',
            'low': '✅'
        }
        
        risk_emoji = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }
        
        parts = []
        
        # Executive summary
        risk_icon = risk_emoji.get(forecast_analysis['risk_level'], '')
        severity_icon = severity_emoji.get(spend_analysis['severity'], '')
        
        parts.append(f"**Financial Status Report**\n")
        
        # Current situation
        if spend_analysis['severity'] != 'low':
            parts.append(
                f"{severity_icon} **SPENDING ALERT**: {spend_analysis['issue']}\n"
                f"The {spend_analysis['category']} category has increased by {spend_analysis['percent_change']:.1f}% "
                f"({spend_analysis['severity']} severity)."
            )
        else:
            parts.append("✅ **SPENDING**: No significant anomalies detected. All categories within budget.")
        
        parts.append("")  # Blank line
        
        # Liquidity status
        days_runway = forecast_analysis['days_to_risk']
        cash_ratio = forecast_analysis['cash_ratio']
        
        if forecast_analysis['risk_level'] == 'critical':
            parts.append(
                f"{risk_icon} **LIQUIDITY ALERT**: Critical cash concern.\n"
                f"At current burn rate, cash will reach minimum threshold in ~{days_runway} days. "
                f"Current cash ratio: {cash_ratio:.1f}x projected needs."
            )
        elif forecast_analysis['risk_level'] == 'high':
            parts.append(
                f"🟠 **LIQUIDITY**: High cash pressure expected.\n"
                f"Runway estimated at {days_runway} days. Monitor closely and prepare mitigation strategies."
            )
        else:
            parts.append(
                f"🟢 **LIQUIDITY**: Healthy cash position.\n"
                f"Sufficient runway for {days_runway}+ days at current burn rate."
            )
        
        parts.append("")  # Blank line
        
        # Recommendation
        action_friendly = self._friendly_action_name(decision_analysis['best_action'])
        confidence_pct = int(decision_analysis['confidence'] * 100)
        
        parts.append(
            f"**RECOMMENDATION**: {action_friendly}\n"
            f"Level: {decision_analysis.get('level_display', decision_analysis.get('level'))}\n"
            f"Decision Margin: {confidence_pct}%\n"
            f"(Top-ranked option vs. runner-up; not model certainty)\n\n"
            f"{decision_analysis['reasoning']}"
        )
        
        narrative = "\n".join(parts)
        return {
            'narrative': narrative,
            'source': 'Template',
            'tone': 'executive',
        }
    
    def _friendly_action_name(self, action):
        """Convert action name to friendly format."""
        names = {
            'do_nothing': 'Maintain Current Strategy',
            'cut_marketing': 'Reduce Marketing Spend',
            'delay_vendor': 'Negotiate Payment Delays',
            'reduce_discretionary': 'Cut Non-Essential Costs',
            'optimize_cloud': 'Optimize Cloud Spend',
            'freeze_hiring': 'Freeze Hiring',
            'rebalance_inventory': 'Rebalance Inventory',
            'tighten_promotions': 'Tighten Promotions',
            'optimize_staffing_mix': 'Optimize Staffing Mix',
            'tighten_procurement': 'Tighten Procurement',
            'defer_capex': 'Defer Capital Expenditure',
            'consolidate_vendors': 'Consolidate Vendors',
        }
        return names.get(action, action.replace('_', ' ').title())
    
    def get_context(self):
        """Get agent context for orchestrator."""
        return {
            'name': self.name,
            'role': 'Executive Communication',
            'responsibility': 'Generate CFO-level briefings and recommendations',
        }


if __name__ == '__main__':
    from data import generate_financial_data, get_budget_config
    from features import build_features
    from agents.spend_agent import SpendIntelligenceAgent
    from agents.forecast_agent import CashFlowForecastAgent
    from agents.decision_agent import DecisionAgent
    
    df = generate_financial_data()
    budget_config = get_budget_config()
    features = build_features(df, budget_config)
    
    spend_agent = SpendIntelligenceAgent()
    forecast_agent = CashFlowForecastAgent(current_cash=150000)
    decision_agent = DecisionAgent()
    
    spend_analysis = spend_agent.analyze(features, budget_config)
    forecast_analysis = forecast_agent.forecast(features)
    decision_analysis = decision_agent.make_decision(spend_analysis, forecast_analysis, features, budget_config)
    
    agent = NarrativeAgent()
    briefing = agent.generate_briefing(spend_analysis, forecast_analysis, decision_analysis)
    
    print("Generated Briefing:")
    print(briefing['narrative'])
