# SYSTEM ARCHITECTURE

## High-Level Flow Diagram

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   STREAMLIT UI (app.py)                                     │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┬─────────────┐ │
│  │ Alert        │ Agent        │ CFO          │ FP&A         │ Compliance   │ Strategic   │ │
│  │ Dashboard    │ Reasoning    │ Briefing     │ Workbench    │ & Close      │ Planning    │ │
│  │ • Alerts     │ • Action Set │ • Narrative  │ • Variance   │ • Exceptions │ • Assumptions│ │
│  │ • Metrics    │ • Comparisons│ • Monte Carlo│ • Scenarios  │ • Reconcile  │ • Outcomes  │ │
│  │ • Charts     │ • Confidence │ • Session    │ • Stress     │ • Close Risk │ • Drivers   │ │
│  └──────────────┴──────────────┴──────────────┴──────────────┴──────────────┴─────────────┘ │
│                                + Overview / Architecture / Impact                            │
└───────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                                │ orchestrator.run_analysis()
                                                ↓
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                               ORCHESTRATOR (orchestrator.py)                                │
│  Coordinates scenario inputs, inference, agents, FP&A, compliance, narration, and UI data  │
└───────┬──────────────────────┬──────────────────────┬──────────────────────┬────────────────┘
        │                      │                      │                      │
        ↓                      ↓                      ↓                      ↓
┌───────────────┐     ┌────────────────┐    ┌────────────────┐    ┌─────────────────────────┐
│   data.py     │     │  features.py   │    │  inference.py  │    │      agents/*.py        │
│               │     │                │    │                │    │                         │
│ Scenario-aware│     │ Finance        │    │ Anomaly        │    │ 1. SpendIntelligence    │
│ transactions  │────→│ feature        │───→│ detection      │───→│ 2. CashFlowForecast     │
│ and payments  │     │ engineering    │    │ Forecasting    │    │ 3. DecisionAgent        │
│               │     │                │    │ Monte Carlo    │    │ 4. NarrativeAgent       │
│ sector        │     │ burn / growth  │    │ ARIMA stress   │    │                         │
│ scale         │     │ budget / MTD   │    │ sensitivity    │    │ Scenario-aware reasoning│
│ macro         │     │ anomaly inputs │    │ liquidity risk │    │ and recommendation      │
│ close pressure│     │                │    │                │    │                         │
└───────────────┘     └────────────────┘    └────────────────┘    └─────────────────────────┘
        │                                                                 │
        │                                                                 ↓
        │                                                    ┌──────────────────────────────┐
        │                                                    │ DECISION + NARRATIVE OUTPUTS │
        │                                                    │                              │
        │                                                    │ • Best action + level        │
        │                                                    │ • Confidence score           │
        │                                                    │ • Top comparisons            │
        │                                                    │ • Available actions          │
        │                                                    │ • Recommended-action sim     │
        │                                                    │ • Executive briefing         │
        │                                                    └──────────────────────────────┘
        │                                                                 │
        └─────────────────────────────────────────────────────────────────┬┘
                                                                          ↓
                                          ┌──────────────────────────────────────────────────┐
                                          │ DOMAIN WORKFLOWS BUILT IN ORCHESTRATOR           │
                                          │                                                  │
                                          │ FP&A                                              │
                                          │ • budgeting and variance analysis                │
                                          │ • forecasting and performance tracking           │
                                          │ • scenario modeling                             │
                                          │ • planning narration                            │
                                          │ • sensitivity analysis                          │
                                          │ • ARIMA stress testing                          │
                                          │                                                  │
                                          │ Compliance & Close                               │
                                          │ • anomaly-driven exception queues               │
                                          │ • auto-reconciliation metrics                   │
                                          │ • review / escalation counts                    │
                                          │ • close risk scoring                            │
                                          │                                                  │
                                          │ Roadmap Extensions                               │
                                          │ • advanced FP&A, treasury, risk, ML, valuation │
                                          │ • tax automation and decision synthesis engine  │
                                          └──────────────────────────────────────────────────┘
                                                                          │
                                                                          ↓
                                          ┌──────────────────────┐   ┌────────────────────────┐
                                          │  memory.py           │   │  evaluation.py         │
                                          │  Decision History    │   │  Accuracy / Health     │
                                          │  Anomaly Log         │   │  Quality Tracking      │
                                          └──────────────────────┘   └────────────────────────┘
```

## Module Responsibilities

### UI Layer (`app.py`)
- Renders the seven-tab CFO-OS interface
- Collects scenario inputs:
  - `Sector`
  - `Business Scale`
  - `Macro Environment`
  - `Close Pressure`
  - `Automation Maturity`
  - `Current Cash Balance`
- Collects advanced assumptions:
  - `Forecast Horizon (days)`
  - `Burn Shock (%)`
  - `Collections Delay (days)`
  - `Monte Carlo Sims`
  - `Revenue Outlook (%)`
  - `Hiring Growth (%)`
  - `Working Capital Efficiency (%)`
- Triggers re-analysis when inputs change

### Data Layer (`data.py`)
- Generates deterministic scenario-aware financial transactions
- Varies transaction count and category mix by:
  - sector
  - business scale
  - macro environment
- Injects deterministic anomaly patterns
- Builds scenario-aware upcoming payment queues
- Changes compliance workload using `close_pressure`

### Feature Engineering (`features.py`)
Input: transaction dataset + budget configuration

Processing:
- compute rolling spend features
- calculate burn-rate history
- track month-to-date budget utilization
- derive category growth and anomaly-facing features

Output: structured finance feature dictionary used by inference and agents

### Inference Layer (`inference.py`)

**1. `detect_anomalies(features)`**
- Algorithm: `IsolationForest`
- Detects category-level overspend anomalies
- Returns normalized anomaly intensity by category

**2. `forecast_cashflow(features, days_ahead, method)`**
- Supports regression and ARIMA-based forecast generation
- Returns forecast series, min cash estimate, and method used
- Feeds downstream stress-testing and scenario modeling

**3. `monte_carlo_cashflow(base_forecast, current_cash, n_simulations, seed)`**
- Generates deterministic simulated cash paths
- Starts at the actual day `0` cash balance
- Returns percentile bands, sample paths, and breach probability

## Agents (`agents/*.py`)

### 1. SpendIntelligenceAgent

```text
INPUT: features, budget_config
PROCESS:
  1. Compute anomaly scores by category
  2. Identify the largest spend issue
  3. Calculate percent change and severity
  4. Produce CFO-readable issue framing

OUTPUT:
  {
    "issue": str,
    "category": str,
    "percent_change": float,
    "severity": str,
    "reason": str,
    "confidence": float
  }
```

### 2. CashFlowForecastAgent

```text
INPUT: features, current_cash, planning assumptions
PROCESS:
  1. Forecast burn and liquidity path
  2. Apply liquidity posture logic
  3. Run Monte Carlo simulation
  4. Run sensitivity analysis
  5. Run ARIMA stress scenarios
  6. Calculate days to risk and ending cash

OUTPUT:
  {
    "risk_level": str,
    "risk_score": float,
    "days_to_risk": int,
    "average_daily_burn": float,
    "projected_ending_cash": float,
    "liquidity_gap": float,
    "forecast_series": [float],
    "forecast_method": str,
    "monte_carlo": {...},
    "sensitivity_analysis": [...],
    "stress_testing": [...]
  }
```

### 3. DecisionAgent

```text
INPUT: spend analysis, forecast analysis, scenario context

SIMULATION LOOP:
  For each available action:
    For each level of that action:
      1. Simulate action impact
      2. Calculate new risk score
      3. Compute business cost
      4. Compute feasibility
      5. Compute reversibility
      6. Score action:

         score = (
             0.5 * risk_reduction
             - 0.2 * business_cost
             + 0.2 * feasibility
             + 0.1 * reversibility
         )

SELECT:
  - Sort all simulations by score
  - Pick best action and second-best action
  - Compute confidence from score gap

OUTPUT:
  {
    "best_action": str,
    "level": float | int,
    "confidence": float,
    "comparisons": [...],
    "available_actions": [...],
    "recommended_action_simulation": {...}
  }
```

Action families include:
- Base: `cut_marketing`, `delay_vendor`, `reduce_discretionary`, `do_nothing`
- Scenario-specific: `optimize_cloud`, `freeze_hiring`, `rebalance_inventory`, `tighten_promotions`, `optimize_staffing_mix`, `tighten_procurement`, `defer_capex`, `consolidate_vendors`

### 4. NarrativeAgent

```text
INPUT: spend_analysis, forecast_analysis, decision_analysis
PROCESS:
  IF OpenAI key available:
    -> Generate richer narration
  ELSE:
    -> Use deterministic executive template

OUTPUT:
  {
    "narrative": str,
    "source": "LLM" | "Template"
  }
```

## Orchestrator (`orchestrator.py`)

Central controller that:
1. Collects scenario inputs and planning assumptions
2. Generates scenario-aware data and payments
3. Builds finance features
4. Runs all four agents
5. Builds FP&A outputs
6. Builds compliance outputs
7. Compiles the final result object for the UI

Primary top-level outputs:
- `spend_intelligence`
- `cashflow_forecast`
- `decision_analysis`
- `executive_briefing`
- `fpa_analysis`
- `compliance_analysis`

## Advanced Capability Roadmap

These modules are good extensions for the platform architecture, but they should be treated as roadmap engines unless explicitly implemented in code.

### Group I — FP&A
- driver-based forecast with DAG propagation
- BvA variance with price-volume-mix decomposition and narration
- KPI benchmarking against peer sets
- cohort survival and LTV modeling using BG/NBD and Gamma-Gamma

### Group II — Risk and Scenarios
- multi-dimensional sensitivity with tornado and spider charts
- elasticity coefficients across key planning drivers
- correlated Monte Carlo with Cholesky structure
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
- dynamic budget consumption rates and `HHI` vendor concentration
- LSTM and ensemble ML cash forecasting
- ML-augmented revenue forecasting with churn prediction

### Group V — Strategy and Valuation
- multi-method `DCF` / `LBO` / comps valuation with football-field output
- `ROIC`, `EVA`, and real-options capital allocation
- full M&A accretion-dilution with synergy modeling

### Group VI — Close and Compliance
- auto-reconciliation plus journal-entry risk scoring
- tax provision automation with `ETR` bridge and Pillar Two impact modeling
- master CFO Decision Synthesis Engine aggregating upstream engines into a prioritized decision brief with confidence-scored reasoning chains

## Data Flow Example

```text
STEP 1: USER INPUTS
  sector = retail
  business_scale = enterprise
  macro_environment = inflationary
  close_pressure = high
  automation_maturity = medium
  current_cash = 300000

STEP 2: DATA GENERATION
  generate_financial_data(...)
  get_upcoming_payments(...)
  -> scenario-specific transactions and payment queue

STEP 3: FEATURES
  build_features(...)
  -> burn rate, category growth, budget utilization, anomaly inputs

STEP 4: INFERENCE
  detect_anomalies(...)
  forecast_cashflow(...)
  monte_carlo_cashflow(...)
  -> anomaly scores, forecast path, stress and simulation outputs

STEP 5: AGENTS
  SpendIntelligenceAgent -> top issue
  CashFlowForecastAgent  -> liquidity risk and forecast outputs
  DecisionAgent          -> best action, comparisons, confidence
  NarrativeAgent         -> CFO briefing

STEP 6: DOMAIN WORKFLOWS
  _build_fpa_analysis(...)
  _build_compliance_analysis(...)

STEP 7: UI OUTPUT
  Seven-tab CFO-OS experience with scenario-aware results
```
