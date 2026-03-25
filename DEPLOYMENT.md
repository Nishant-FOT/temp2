# DEPLOYMENT GUIDE

## System Flow

```text
Zaggle Transaction Exports -> Feature Engineering -> Inference Models -> Agentic Orchestrator
                     -> FP&A / Compliance Workflows -> Generative Narration -> CFO UI
```

## Runtime Layout

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

## Local Launch

### Install Dependencies

```bash
cd /Users/hemang/Desktop/BOOKS/code/cfo_os
pip install -r requirements.txt
```

### Launch the UI

```bash
streamlit run app.py
```

Open `http://localhost:8501`.

## Alternative Commands

### Launch Script

```bash
./launch.sh
```

### CLI Analysis

```bash
python3 orchestrator.py
```

### Integration Test

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

These inputs feed the orchestrator directly, so scenario changes propagate into forecasting, decisioning, FP&A, and compliance outputs.

## Execution Path

When the user clicks `Run Analysis`, the system:
1. generates scenario-aware transactions and upcoming payments
2. builds finance features
3. runs anomaly detection and cashflow forecasting
4. runs the agentic decision engine
5. compiles FP&A and compliance workflows
6. produces executive narration
7. renders the final outputs in Streamlit

## Product Modules

### `🚨 Alert Dashboard`
- top alerts
- key metrics
- anomaly and forecast visuals

### `🤖 Agent Reasoning`
- scored action comparison matrix
- recommendation and confidence
- scenario-specific available actions

### `📋 CFO Briefing`
- executive summary
- session metadata
- Monte Carlo baseline vs recommended-action charts

### `📐 FP&A Workbench`
- variance analysis
- KPI and performance tracking
- scenario modeling
- sensitivity analysis
- ARIMA stress testing
- planning narration

### `🧭 Overview`
- concept note
- architecture summary
- expected business impact

### `🧾 Compliance & Close`
- flagged transaction review
- reconciliation queue
- auto-match metrics
- escalations and close risk

### `🗺️ Strategic Planning`
- planning assumption tracking
- outcome linkage
- strategic driver view

## Forecasting and Decisioning

### Forecast Stack
- regression-based forecast generation
- ARIMA-based stress support
- deterministic Monte Carlo simulation
- sensitivity analysis
- liquidity-aware burn adjustments
- recommended-action cashflow comparison

### Decision Engine

The recommendation layer scores action-level combinations with:

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

## Example Programmatic Run

```python
from orchestrator import CFOOrchestrator

orchestrator = CFOOrchestrator(
    current_cash=300000,
    sector="manufacturing",
    business_scale="enterprise",
    macro_environment="inflationary",
    close_pressure="quarter_end",
    automation_maturity="low",
    planning_assumptions={
        "forecast_horizon_days": 60,
        "burn_shock_pct": 0.10,
        "collections_delay_days": 10,
        "monte_carlo_sims": 500,
        "revenue_outlook_pct": -0.10,
        "hiring_growth_pct": 0.05,
        "working_capital_efficiency": 0.05,
    },
)

result = orchestrator.run_analysis()
```

## Troubleshooting

### Streamlit Not Installed

```bash
pip install streamlit
```

### Import Errors

Run commands from the project root:

```bash
cd /Users/hemang/Desktop/BOOKS/code/cfo_os
```

### Narrative Generation Fallback

If OpenAI credentials are not configured, the app falls back to deterministic template narration.

### Results Look Stale

Change inputs and run analysis again. The app compares current controls with the stored result payload and refreshes when they differ.

## Validation

Before demoing or packaging the prototype:

```bash
python3 -m py_compile app.py orchestrator.py data.py features.py inference.py agents/*.py
python3 test_system.py
```

## Related Docs

- [README.md](/Users/hemang/Desktop/BOOKS/code/cfo_os/README.md)
- [ARCHITECTURE.md](/Users/hemang/Desktop/BOOKS/code/cfo_os/ARCHITECTURE.md)
- [QUICKSTART.md](/Users/hemang/Desktop/BOOKS/code/cfo_os/QUICKSTART.md)
