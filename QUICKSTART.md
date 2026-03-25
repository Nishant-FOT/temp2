# QUICKSTART

## System Flow

```text
Zaggle Transaction Exports -> Feature Engineering -> Inference Models -> Agentic Orchestrator
                     -> FP&A / Compliance Workflows -> Generative Narration -> CFO UI
```

## Product Layout

```text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              STREAMLIT UI (app.py)                                 │
│  Alert Dashboard | Agent Reasoning | CFO Briefing | FP&A Workbench                 │
│  Overview | Compliance & Close | Strategic Planning                                │
└───────────────────────────────────┬─────────────────────────────────────────────────┘
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR (orchestrator.py)                               │
│  Scenario inputs -> data -> features -> inference -> agents -> domain workflows    │
└──────────────┬─────────────────┬─────────────────┬──────────────────┬──────────────┘
               ↓                 ↓                 ↓                  ↓
         ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌────────────┐
         │ data.py  │      │features.py│     │inference.py│     │ agents/*.py │
         └──────────┘      └──────────┘      └──────────┘      └────────────┘
```

## Project Structure

```text
cfo_os/
├── app.py
├── orchestrator.py
├── data.py
├── features.py
├── inference.py
├── memory.py
├── evaluation.py
├── test_system.py
├── launch.sh
├── requirements.txt
├── README.md
├── ARCHITECTURE.md
├── QUICKSTART.md
├── DEPLOYMENT.md
└── agents/
    ├── spend_agent.py
    ├── forecast_agent.py
    ├── decision_agent.py
    └── narrative_agent.py
```

## Start the Prototype

### Install Dependencies

```bash
cd /Users/hemang/Desktop/BOOKS/code/cfo_os
pip install -r requirements.txt
```

### Launch the UI

```bash
streamlit run app.py
```

Then open `http://localhost:8501`.

### Run the CLI Pipeline

```bash
python3 orchestrator.py
```

### Run the Integration Test

```bash
python3 test_system.py
```

## Runtime Inputs

Primary scenario controls:
- `Sector`
- `Business Scale`
- `Macro Environment`
- `Close Pressure`
- `Automation Maturity`
- `Current Cash Balance`

Advanced assumptions:
- `Forecast Horizon (days)`
- `Burn Shock (%)`
- `Collections Delay (days)`
- `Monte Carlo Sims`
- `Revenue Outlook (%)`
- `Hiring Growth (%)`
- `Working Capital Efficiency (%)`

These values are connected to the analysis pipeline, so outputs change across iterations.

## UI Navigation

### `🚨 Alert Dashboard`
- headline alerts
- anomaly and liquidity metrics
- core charts

### `🤖 Agent Reasoning`
- scenario-specific action set
- comparison matrix
- recommendation and confidence

### `📋 CFO Briefing`
- executive narration
- session metadata
- Monte Carlo baseline vs recommended-action visuals

### `📐 FP&A Workbench`
- variance analysis
- KPI tracking
- scenario modeling
- sensitivity analysis
- ARIMA stress testing

### `🧭 Overview`
- concept note
- architecture
- business impact

### `🧾 Compliance & Close`
- exception queues
- reconciliation metrics
- review and escalation counts
- close risk

### `🗺️ Strategic Planning`
- planning assumptions
- outcome linkage
- strategic driver view

## Decision Logic

The recommendation layer simulates actions across levels and scores them using:

```python
score = (
    0.5 * risk_reduction
    - 0.2 * business_cost
    + 0.2 * feasibility
    + 0.1 * reversibility
)
```

Base actions:
- `cut_marketing`
- `delay_vendor`
- `reduce_discretionary`
- `do_nothing`

Scenario-specific actions may include:
- `optimize_cloud`
- `freeze_hiring`
- `rebalance_inventory`
- `tighten_promotions`
- `optimize_staffing_mix`
- `tighten_procurement`
- `defer_capex`
- `consolidate_vendors`

## Forecasting Stack

The forecast layer includes:
- burn and runway estimation
- projected ending cash
- liquidity gap
- deterministic Monte Carlo simulation
- sensitivity analysis
- ARIMA stress testing
- recommended-action cashflow comparison

## Example Usage

```python
from orchestrator import CFOOrchestrator

orch = CFOOrchestrator(
    current_cash=250000,
    sector="saas",
    business_scale="startup",
    macro_environment="stable",
    close_pressure="medium",
    automation_maturity="high",
    planning_assumptions={
        "forecast_horizon_days": 45,
        "burn_shock_pct": 0.05,
        "collections_delay_days": 5,
        "monte_carlo_sims": 300,
        "revenue_outlook_pct": 0.05,
        "hiring_growth_pct": 0.00,
        "working_capital_efficiency": 0.10,
    },
)

result = orch.run_analysis()
print(result["decision_analysis"]["best_action"])
```

## Notes

- The dataset is synthetic, but scenario-aware rather than globally fixed.
- Narrative generation supports an optional OpenAI-backed path and a deterministic fallback.
- Compliance and close outputs are designed to move with scenario and planning inputs.
