"""
Inference Layer
Anomaly detection and cashflow forecasting.
"""
import numpy as np
import pandas as pd
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
    
    for category in features['categories']:
        key = f'rolling_7day_{category}'
        if key in features:
            spend_data = features[key].reshape(-1, 1)
            
            # Skip if too few samples
            if len(spend_data) < 5:
                anomaly_scores[category] = 0.0
                continue
            
            # Fit IsolationForest
            iso_forest = IsolationForest(contamination=min(contamination, 0.3), random_state=42)
            predictions = iso_forest.fit_predict(spend_data)
            
            # Score: -1 is anomaly, 1 is normal
            # Normalize to 0-1 range
            scores = iso_forest.score_samples(spend_data)
            anomaly_score = 1 - (1 / (1 + np.exp(scores[-1])))  # Sigmoid normalization
            anomaly_scores[category] = max(0, min(1, anomaly_score))
    
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
    
    for category in features['categories']:
        key = f'rolling_7day_{category}'
        if key in features:
            data = features[key]
            if len(data) > 1:
                z_scores = np.abs(stats.zscore(data))
                is_anomaly = z_scores[-1] > threshold
                anomaly_indicators[category] = 1.0 if is_anomaly else 0.0
            else:
                anomaly_indicators[category] = 0.0
    
    return anomaly_indicators


def forecast_cashflow(features, days_ahead=30, method='regression'):
    """
    Forecast cashflow for next N days.
    
    Args:
        features: Features dict
        days_ahead: Number of days to forecast
        method: 'arima' or 'regression'
        
    Returns:
        Dict with forecast series and risk metrics
    """
    burn_rate = features['burn_rate']
    
    if len(burn_rate) < 5:
        # Not enough data for sophisticated forecasting
        baseline_burn = np.mean(burn_rate[-3:]) if len(burn_rate) > 0 else 10000
        forecast = [baseline_burn] * days_ahead
        method_used = 'baseline'
    elif method == 'arima':
        try:
            arima_model = ARIMA(burn_rate, order=(1, 1, 1))
            arima_fit = arima_model.fit()
            forecast = arima_fit.forecast(steps=days_ahead).tolist()
            forecast = [max(5000, float(value)) for value in forecast]
            method_used = 'arima'
        except Exception:
            method = 'regression'
            forecast = None
    else:
        forecast = None

    if forecast is None:
        # Simple linear regression fallback (ARIMA not used due to complexity)
        x = np.arange(len(burn_rate))
        y = burn_rate
        
        # Fit polynomial of degree 2
        coeffs = np.polyfit(x, y, 2)
        poly = np.poly1d(coeffs)
        
        # Forecast
        future_x = np.arange(len(burn_rate), len(burn_rate) + days_ahead)
        forecast = poly(future_x).tolist()
        forecast = [max(5000, f) for f in forecast]  # Minimum burn rate threshold
        method_used = 'regression'
    
    # Estimate minimum cash needed
    total_projected_spend = sum(forecast) / len(forecast) if forecast else 0
    min_cash_needed = total_projected_spend * 7  # Cover 7 days of spending
    
    # Find risk window (when burn rate is highest)
    forecast_array = np.array(forecast)
    risk_window_days = np.argmax(forecast_array[:7]) + 1 if len(forecast_array) > 0 else 1
    
    return {
        'forecast_series': forecast,
        'min_cash': min_cash_needed,
        'risk_window_days': risk_window_days,
        'average_daily_burn': np.mean(forecast) if forecast else 0,
        'method_used': method_used,
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
    forecast = np.array(base_forecast, dtype=float)
    if forecast.size == 0:
        return {
            'days': [0],
            'p10_cash': [current_cash],
            'p50_cash': [current_cash],
            'p90_cash': [current_cash],
            'sample_paths': [],
            'breach_probability': 0.0,
            'full_horizon_breach_probability': 0.0,
            'warning_horizon_days': 0,
            'median_end_cash': current_cash,
            'p10_end_cash': current_cash,
            'p90_end_cash': current_cash,
        }

    day_over_day_changes = np.diff(forecast) / np.maximum(forecast[:-1], 1.0)
    volatility = float(np.std(day_over_day_changes)) if day_over_day_changes.size > 0 else 0.05
    volatility = min(0.22, max(0.04, volatility))

    rng = np.random.default_rng(seed)
    cash_paths = []

    for _ in range(n_simulations):
        scenario_bias = rng.normal(0, volatility / 2)
        daily_noise = rng.normal(0, volatility, size=forecast.size)
        scenario_burn = forecast * (1 + scenario_bias + daily_noise)
        scenario_burn = np.clip(scenario_burn, 5000, None)
        cash_path = current_cash - np.cumsum(scenario_burn)
        cash_paths.append(np.concatenate(([current_cash], cash_path)))

    cash_paths = np.array(cash_paths)
    percentiles = np.percentile(cash_paths, [10, 50, 90], axis=0)
    baseline_cash_path = current_cash - np.cumsum(forecast)
    breached_days = np.where(baseline_cash_path < 0)[0]
    expected_runway_days = int(breached_days[0] + 1) if breached_days.size > 0 else int(forecast.size)
    warning_horizon_days = min(max(1, int(np.ceil(expected_runway_days / 2))), int(forecast.size))
    near_term_breach_probability = float(
        np.mean(np.any(cash_paths[:, :warning_horizon_days + 1] < 0, axis=1))
    )
    full_horizon_breach_probability = float(np.mean(np.any(cash_paths < 0, axis=1)))
    breach_probability_curve = [
        round(float(np.mean(np.any(cash_paths[:, :day + 1] < 0, axis=1))), 3)
        for day in range(0, cash_paths.shape[1])
    ]

    return {
        'days': list(range(0, forecast.size + 1)),
        'p10_cash': percentiles[0].round(2).tolist(),
        'p50_cash': percentiles[1].round(2).tolist(),
        'p90_cash': percentiles[2].round(2).tolist(),
        'sample_paths': cash_paths[:25].round(2).tolist(),
        'breach_probability': round(near_term_breach_probability, 3),
        'full_horizon_breach_probability': round(full_horizon_breach_probability, 3),
        'breach_probability_curve': breach_probability_curve,
        'warning_horizon_days': int(warning_horizon_days),
        'median_end_cash': round(float(percentiles[1, -1]), 2),
        'p10_end_cash': round(float(percentiles[0, -1]), 2),
        'p90_end_cash': round(float(percentiles[2, -1]), 2),
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


if __name__ == '__main__':
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
    print(f"  Min cash needed: ${forecast['min_cash']:,.2f}")
    print(f"  Risk window: {forecast['risk_window_days']} days")
    print(f"  Average daily burn: ${forecast['average_daily_burn']:,.2f}")
