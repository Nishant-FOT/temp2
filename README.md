# AI-Native CFO Operating System

An interactive CFO platform that combines spend intelligence, cashflow forecasting, agentic decisioning, FP&A automation, compliance workflows, and executive narration in a single Streamlit app.

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

## Current Modules

### UI (`app.py`)
- `🚨 Alert Dashboard`
- `🤖 Agent Reasoning`
- `📋 CFO Briefing`
- `📐 FP&A Workbench`
- `🧭 Overview`
- `🧾 Compliance & Close`
- `🗺️ Strategic Planning`

### Data and Features
- `data.py`: scenario-aware transaction and payment generation
- `features.py`: burn, growth, budget, and anomaly-oriented feature engineering

### Inference
- `inference.py`: anomaly detection, forecasting, Monte Carlo simulation, ARIMA stress support

### Agents
- `SpendIntelligenceAgent`
- `CashFlowForecastAgent`
- `DecisionAgent`
- `NarrativeAgent`

### Supporting Layers
- `orchestrator.py`: pipeline coordination and output assembly
- `memory.py`: anomaly and decision history
- `evaluation.py`: quality and health tracking

## Scenario Inputs

Primary controls:
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

These inputs are connected to the runtime pipeline, so outputs change across iterations.

## Core Capabilities

### Real-Time Spend Intelligence
- anomaly detection over scenario-aware transaction data
- category-level overspend identification
- severity and confidence scoring

### Cashflow Forecasting and Optimization
- liquidity-aware burn modeling
- projected ending cash and runway analysis
- deterministic Monte Carlo simulation
- ARIMA stress testing
- baseline vs recommended-action comparison

### FP&A Automation
- budgeting and variance analysis
- forecasting and performance tracking
- scenario modeling
- planning narration
- sensitivity analysis

### Compliance and Close
- exception queues
- reconciliation queues
- auto-match metrics
- review and escalation counts
- close risk scoring

### Strategic Planning
- links revenue, hiring, working-capital, and automation assumptions to outcomes

## Advanced Expansion Roadmap

The following capability groups would make the platform materially stronger as a broader CFO operating system. They should be treated as roadmap modules unless explicitly implemented in code.

### Group I — FP&A
- driver-based forecasting with DAG propagation
- BvA variance with price-volume-mix decomposition and LLM narration
- KPI benchmarking against peer sets
- cohort survival and LTV modeling with BG/NBD and Gamma-Gamma

### Group II — Risk and Scenarios
- tornado and spider-chart sensitivity analysis
- elasticity coefficients across key drivers
- correlated Monte Carlo using a Cholesky structure
- forward and reverse stress testing
- scenario decision trees
- corporate `VaR`, `CVaR`, `EaR`, and `CFaR`

### Group III — Treasury and Cash
- 13-week direct-method rolling forecast
- genetic-algorithm cash optimization
- working-capital liberation modeling from `CCC -> cash`
- capital structure and `WACC` optimization
- FX and commodity hedge programme management

### Group IV — ML and Intelligence
- Isolation Forest plus autoencoder anomaly detection
- budget consumption rates and `HHI` vendor concentration
- LSTM and ensemble ML cash forecasting
- ML-augmented revenue forecasting with churn prediction

### Group V — Strategy and Valuation
- multi-method `DCF` / `LBO` / comps valuation with football-field output
- `ROIC`, `EVA`, and real-options capital allocation
- full M&A accretion-dilution and synergy modeling

### Group VI — Close and Compliance
- auto-reconciliation plus journal-entry risk scoring
- tax provision automation with `ETR` bridge and Pillar Two impact modeling
- a master CFO Decision Synthesis Engine that aggregates upstream engines into a prioritized decision brief with confidence-scored reasoning chains

## Decision Engine

The recommendation layer simulates action-level combinations and scores them using a CFO-style trade-off function:

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

Scenario-specific actions may also include:
- `optimize_cloud`
- `freeze_hiring`
- `rebalance_inventory`
- `tighten_promotions`
- `optimize_staffing_mix`
- `tighten_procurement`
- `defer_capex`
- `consolidate_vendors`

The engine returns:
- best action
- recommended level
- confidence based on the score gap
- top comparison set
- available actions for the current scenario
- recommended-action cashflow simulation

## Quick Start

### Install

```bash
cd /Users/hemang/Desktop/cfo_os
pip install -r requirements.txt
```

### Launch the UI

```bash
streamlit run APP PATH
```

Then open `http://localhost:8501`.

### Run CLI Analysis

```bash
python3 orchestrator.py
```

### Run Integration Test

```bash
python3 test_system.py
```

## Example Usage

```python
from orchestrator import CFOOrchestrator

orchestrator = CFOOrchestrator(
    current_cash=180000,
    sector="retail",
    business_scale="enterprise",
    macro_environment="inflationary",
    close_pressure="high",
    automation_maturity="medium",
    planning_assumptions={
        "forecast_horizon_days": 60,
        "burn_shock_pct": 0.10,
        "collections_delay_days": 5,
        "monte_carlo_sims": 400,
        "revenue_outlook_pct": -0.05,
        "hiring_growth_pct": 0.05,
        "working_capital_efficiency": 0.10,
    },
)

result = orchestrator.run_analysis()
```

## Output Domains

`run_analysis()` returns:
- `spend_intelligence`
- `cashflow_forecast`
- `decision_analysis`
- `executive_briefing`
- `fpa_analysis`
- `compliance_analysis`

It also includes scenario metadata such as sector, scale, macro environment, close pressure, automation maturity, and planning assumptions.

## Related Docs

- [ARCHITECTURE.md](/Users/hemang/Desktop/BOOKS/code/cfo_os/ARCHITECTURE.md)
- [QUICKSTART.md](/Users/hemang/Desktop/BOOKS/code/cfo_os/QUICKSTART.md)
- [DEPLOYMENT.md](/Users/hemang/Desktop/BOOKS/code/cfo_os/DEPLOYMENT.md)
