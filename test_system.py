#!/usr/bin/env python3
"""
Quick integration test for CFO system.
"""

print("=" * 60)
print("INTEGRATION TEST - AI-NATIVE CFO OPERATING SYSTEM")
print("=" * 60)

# Test imports
print("\n[1/5] Testing imports...")
try:
    from data import generate_financial_data, get_budget_config
    from features import build_features
    from agents.spend_agent import SpendIntelligenceAgent
    from agents.forecast_agent import CashFlowForecastAgent
    from agents.decision_agent import DecisionAgent
    from agents.narrative_agent import NarrativeAgent
    from orchestrator import CFOOrchestrator
    print("✅ All modules imported successfully")
except Exception as e:
    print(f"❌ Import failed: {e}")
    exit(1)

# Test data generation
print("\n[2/5] Testing data generation...")
try:
    df = generate_financial_data(days=90)
    budget = get_budget_config()
    print(f"✅ Generated {len(df)} transactions")
    print(f"   Categories: {df['category'].unique().tolist()}")
except Exception as e:
    print(f"❌ Data generation failed: {e}")
    exit(1)

# Test feature engineering
print("\n[3/5] Testing feature engineering...")
try:
    features = build_features(df, budget)
    print(f"✅ Engineered features for {len(features['categories'])} categories")
    print(f"   Category growth: {features['category_growth']}")
except Exception as e:
    print(f"❌ Feature engineering failed: {e}")
    exit(1)

# Test agents
print("\n[4/5] Testing multi-agent pipeline...")
try:
    spend_agent = SpendIntelligenceAgent()
    spend_result = spend_agent.analyze(features, budget)
    print(f"✅ Spend agent: {spend_result['severity']} severity detected")
    
    forecast_agent = CashFlowForecastAgent(current_cash=700000)
    forecast_result = forecast_agent.forecast(features)
    print(f"✅ Forecast agent: {forecast_result['risk_level']} risk level")
    
    decision_agent = DecisionAgent()
    decision_result = decision_agent.make_decision(spend_result, forecast_result, features, budget)
    print(f"✅ Decision agent: recommended '{decision_result['best_action']}'")
    
    narrative_agent = NarrativeAgent()
    narrative_result = narrative_agent.generate_briefing(spend_result, forecast_result, decision_result)
    print(f"✅ Narrative agent: generated {len(narrative_result['narrative'])} character briefing")
except Exception as e:
    print(f"❌ Agent pipeline failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test orchestrator
print("\n[5/5] Testing orchestrator...")
try:
    orchestrator = CFOOrchestrator(current_cash=700000)
    result = orchestrator.run_analysis(days=90)
    print(f"✅ Orchestrator complete")
    print(f"   Session: {result['session_id']}")
    print(f"   Best action: {result['decision_analysis']['best_action']}")
    print(f"   Decision margin: {result['decision_analysis']['confidence']:.0%}")
except Exception as e:
    print(f"❌ Orchestrator failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED - SYSTEM READY FOR DEPLOYMENT")
print("=" * 60)
print("\nTo launch the Streamlit UI, run:")
print("  streamlit run app.py")
