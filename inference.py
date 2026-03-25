"""
Inference Layer
Anomaly detection and cashflow forecasting.
"""

import numpy as np
from sklearn.ensemble import IsolationForest
from scipy import stats
from statsmodels.tsa.arima.model import ARIMA


def detect_anomalies(features, contamination=0.1):
    """
    Detect spending anomalies using IsolationForest.

    Args:
        features: Features dict from features.py
        contamination: Expected proportion of anomalies

    Returns:
        Dict with anomaly scores per category
    """
    anomaly_scores = {}

    categories = features.get("categories", [])
    for category in categories:
        key = f"rolling_7day_{category}"
        if key not in features:
            continue

        spend_data = np.asarray(features[key], dtype=float).reshape(-1, 1)

        if len(spend_data) < 5:
            anomaly_scores[category] = 0.0
            continue

        iso_forest = IsolationForest(
            contamination=min(contamination, 0.3),
            random_state=42
        )
        iso_forest.fit(spend_data)

        scores = iso_forest.score_samples(spend_data)
        latest_score = float(scores[-1])

        anomaly_score = 1.0 / (1.0 + np.exp(3.0 * latest_score))
        anomaly_scores[category] = float(np.clip(anomaly_score, 0.0, 1.0))

    return anomaly_scores


def detect_anomalies_zscore(features, threshold=2.5):
    """
    Alternative anomaly detection using Z-score.

    Args:
        features: Features dict
        threshold: Z-score threshold for anomaly

    Returns:
        Dict with anomaly flags per category
    """
    anomaly_indicators = {}

    categories = features.get("categories", [])
    for category in categories:
        key = f"rolling_7day_{category}"
        if key not in features:
            continue

        data = np.asarray(features[key], dtype=float)
        if len(data) > 1:
            z_scores = np.abs(stats.zscore(data, nan_policy="omit"))
            latest_z = z_scores[-1] if len(z_scores) else 0.0
            if np.isnan(latest_z):
                latest_z = 0.0
            anomaly_indicators[category] = 1.0 if latest_z > threshold else 0.0
        else:
            anomaly_indicators[category] = 0.0

    return anomaly_indicators


def _safe_burn_floor(burn_rate):
    if len(burn_rate) == 0:
        return 0.0
    recent = np.asarray(burn_rate[-14:], dtype=float)
    positive_recent = recent[recent > 0]
    if len(positive_recent) == 0:
        return 0.0
    return max(0.0, float(np.percentile(positive_recent, 15)))


def _linear_trend_forecast(burn_rate, days_ahead):
    recent = np.asarray(burn_rate[-21:] if len(burn_rate) >= 21 else burn_rate, dtype=float)

    if len(recent) == 0:
        return [10000.0] * days_ahead, "baseline"

    if len(recent) < 4:
        base = float(np.mean(recent))
        return [round(max(0.0, base), 2)] * days_ahead, "baseline"

    base = float(np.mean(recent[-7:]))
    x = np.arange(len(recent), dtype=float)

    slope = float(np.polyfit(x, recent, 1)[0]) if len(recent) >= 5 else 0.0

    max_daily_change = max(abs(base) * 0.03, 100.0)
    slope = float(np.clip(slope, -max_daily_change, max_daily_change))

    floor_value = _safe_burn_floor(recent)

    forecast = []
    for day in range(1, days_ahead + 1):
        value = base + slope * day
        value = max(floor_value, value)
        forecast.append(round(float(value), 2))

    return forecast, "linear_trend"


def forecast_cashflow(features, days_ahead=30, method="regression"):
    """
    Forecast cashflow for next N days.

    Args:
        features: Features dict
        days_ahead: Number of days to forecast
        method: 'arima' or 'regression'

    Returns:
        Dict with forecast series and risk metrics
    """
    burn_rate = np.asarray(features.get("burn_rate", []), dtype=float)
    burn_rate = burn_rate[np.isfinite(burn_rate)]

    if len(burn_rate) < 5:
        baseline_burn = float(np.mean(burn_rate[-3:])) if len(burn_rate) > 0 else 10000.0
        baseline_burn = max(0.0, baseline_burn)
        forecast = [round(baseline_burn, 2)] * days_ahead
        method_used = "baseline"
    elif method == "arima":
        try:
            arima_model = ARIMA(burn_rate, order=(1, 1, 1))
            arima_fit = arima_model.fit()
            arima_forecast = arima_fit.forecast(steps=days_ahead)

            floor_value = _safe_burn_floor(burn_rate)
            forecast = [round(float(max(floor_value, value)), 2) for value in arima_forecast]
            method_used = "arima"
        except Exception:
            forecast, method_used = _linear_trend_forecast(burn_rate, days_ahead)
    else:
        forecast, method_used = _linear_trend_forecast(burn_rate, days_ahead)

    average_projected_burn = float(np.mean(forecast)) if forecast else 0.0
    min_cash_needed = average_projected_burn * 7

    forecast_array = np.asarray(forecast, dtype=float)
    lookahead = forecast_array[: min(7, len(forecast_array))]
    risk_window_days = int(np.argmax(lookahead) + 1) if len(lookahead) > 0 else 1

    return {
        "forecast_series": forecast,
        "forecast_values": forecast,
        "min_cash": round(min_cash_needed, 2),
        "risk_window_days": risk_window_days,
        "average_daily_burn": round(average_projected_burn, 2),
        "method_used": method_used,
    }


def monte_carlo_cashflow(base_forecast, current_cash, n_simulations=250, seed=42):
    """
    Run deterministic Monte Carlo simulations around the forecast burn path.

    Args:
        base_forecast: List of forecast daily burn values
        current_cash: Current cash balance
        n_simulations: Number of scenarios to generate
        seed: Fixed seed for deterministic UI output

    Returns:
        Dict with percentile paths, sample cash paths, and risk statistics
    """
    forecast = np.asarray(base_forecast, dtype=float)

    if forecast.size == 0:
        return {
            "days": [0],
            "p10_cash": [current_cash],
            "p50_cash": [current_cash],
            "p90_cash": [current_cash],
            "sample_paths": [],
            "breach_probability": 0.0,
            "full_horizon_breach_probability": 0.0,
            "breach_probability_curve": [0.0],
            "warning_horizon_days": 0,
            "median_end_cash": current_cash,
            "p10_end_cash": current_cash,
            "p90_end_cash": current_cash,
        }

    safe_denominator = np.maximum(np.abs(forecast[:-1]), 1.0)
    day_over_day_changes = np.diff(forecast) / safe_denominator
    volatility = float(np.std(day_over_day_changes)) if day_over_day_changes.size > 0 else 0.05
    volatility = min(0.18, max(0.02, volatility))

    floor_value = _safe_burn_floor(forecast)

    rng = np.random.default_rng(seed)
    cash_paths = []

    for _ in range(n_simulations):
        scenario_bias = rng.normal(0, volatility / 3)
        daily_noise = rng.normal(0, volatility, size=forecast.size)

        scenario_burn = forecast * (1 + scenario_bias + daily_noise)
        scenario_burn = np.clip(scenario_burn, floor_value, None)

        cash_path = current_cash - np.cumsum(scenario_burn)
        cash_paths.append(np.concatenate(([current_cash], cash_path)))

    cash_paths = np.asarray(cash_paths, dtype=float)
    percentiles = np.percentile(cash_paths, [10, 50, 90], axis=0)

    baseline_cash_path = current_cash - np.cumsum(forecast)
    breached_days = np.where(baseline_cash_path < 0)[0]
    expected_runway_days = int(breached_days[0] + 1) if breached_days.size > 0 else int(forecast.size)

    warning_horizon_days = min(
        max(1, int(np.ceil(expected_runway_days / 2))),
        int(forecast.size)
    )

    near_term_breach_probability = float(
        np.mean(np.any(cash_paths[:, :warning_horizon_days + 1] < 0, axis=1))
    )
    full_horizon_breach_probability = float(np.mean(np.any(cash_paths < 0, axis=1)))

    breach_probability_curve = [
        round(float(np.mean(np.any(cash_paths[:, :day + 1] < 0, axis=1))), 3)
        for day in range(cash_paths.shape[1])
    ]

    return {
        "days": list(range(0, forecast.size + 1)),
        "p10_cash": percentiles[0].round(2).tolist(),
        "p50_cash": percentiles[1].round(2).tolist(),
        "p90_cash": percentiles[2].round(2).tolist(),
        "sample_paths": cash_paths[:25].round(2).tolist(),
        "breach_probability": round(near_term_breach_probability, 3),
        "full_horizon_breach_probability": round(full_horizon_breach_probability, 3),
        "breach_probability_curve": breach_probability_curve,
        "warning_horizon_days": int(warning_horizon_days),
        "median_end_cash": round(float(percentiles[1, -1]), 2),
        "p10_end_cash": round(float(percentiles[0, -1]), 2),
        "p90_end_cash": round(float(percentiles[2, -1]), 2),
    }


def calculate_risk_score(
    min_cash_projected,
    current_cash=100000,
    days_to_risk=None,
    forecast_horizon_days=None,
):
    """
    Calculate risk score based on liquidity buffer and runway coverage.

    Args:
        min_cash_projected: Minimum cash needed over forecast period
        current_cash: Current cash balance
        days_to_risk: Estimated number of days before cash is exhausted
        forecast_horizon_days: Number of forecast days in view

    Returns:
        Risk score 0-1
    """
    if min_cash_projected <= 0:
        buffer_risk = 0.0
    else:
        ratio = current_cash / min_cash_projected

        if ratio > 1.5:
            buffer_risk = 0.0
        elif ratio > 1.0:
            buffer_risk = 0.2
        elif ratio > 0.8:
            buffer_risk = 0.5
        elif ratio > 0.5:
            buffer_risk = 0.75
        else:
            buffer_risk = 1.0

    if days_to_risk is None or forecast_horizon_days in (None, 0):
        return buffer_risk

    runway_ratio = max(0.0, min(float(days_to_risk) / float(forecast_horizon_days), 1.0))

    if days_to_risk <= 7:
        runway_risk = 1.0
    elif runway_ratio >= 1.0:
        runway_risk = 0.0
    elif runway_ratio >= 0.75:
        runway_risk = 0.25
    elif runway_ratio >= 0.5:
        runway_risk = 0.5
    elif runway_ratio >= 0.25:
        runway_risk = 0.75
    else:
        runway_risk = 1.0

    return max(buffer_risk, runway_risk)


if __name__ == "__main__":
    from data import generate_financial_data, get_budget_config
    from features import build_features

    df = generate_financial_data()
    budget_config = get_budget_config()
    features = build_features(df, budget_config)

    print("Anomaly Detection (IsolationForest):")
    anomalies = detect_anomalies(features)
    for cat, score in anomalies.items():
        print(f"  {cat}: {score:.3f}")

    print("\nCashflow Forecast:")
    forecast = forecast_cashflow(features)
    print(f"  Method used: {forecast['method_used']}")
    print(f"  Min cash needed: ${forecast['min_cash']:,.2f}")
    print(f"  Risk window: {forecast['risk_window_days']} days")
    print(f"  Average daily burn: ${forecast['average_daily_burn']:,.2f}")
