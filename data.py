"""
Data Generation Module
Generate synthetic financial dataset for CFO simulation.
"""
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import hashlib
from connectors.zaggle_client import load_zaggle_transactions


SECTOR_PROFILES = {
    'saas': {
        'transaction_multiplier': 1.0,
        'category_spend_multiplier': {
            'payroll': 1.0,
            'operations': 0.8,
            'tech': 1.35,
            'marketing': 1.2,
        },
        'anomaly_category': 'marketing',
    },
    'retail': {
        'transaction_multiplier': 1.8,
        'category_spend_multiplier': {
            'payroll': 1.15,
            'operations': 1.45,
            'tech': 0.85,
            'marketing': 1.05,
        },
        'anomaly_category': 'operations',
    },
    'healthcare': {
        'transaction_multiplier': 1.25,
        'category_spend_multiplier': {
            'payroll': 1.3,
            'operations': 1.1,
            'tech': 1.0,
            'marketing': 0.75,
        },
        'anomaly_category': 'payroll',
    },
    'manufacturing': {
        'transaction_multiplier': 1.55,
        'category_spend_multiplier': {
            'payroll': 1.2,
            'operations': 1.5,
            'tech': 0.9,
            'marketing': 0.8,
        },
        'anomaly_category': 'operations',
    },
    'fintech': {
        'transaction_multiplier': 1.35,
        'category_spend_multiplier': {
            'payroll': 1.1,
            'operations': 0.9,
            'tech': 1.55,
            'marketing': 0.95,
        },
        'anomaly_category': 'tech',
    },
    'logistics': {
        'transaction_multiplier': 1.7,
        'category_spend_multiplier': {
            'payroll': 1.1,
            'operations': 1.6,
            'tech': 0.95,
            'marketing': 0.7,
        },
        'anomaly_category': 'operations',
    },
    'hospitality': {
        'transaction_multiplier': 1.9,
        'category_spend_multiplier': {
            'payroll': 1.25,
            'operations': 1.35,
            'tech': 0.75,
            'marketing': 1.15,
        },
        'anomaly_category': 'operations',
    },
    'education': {
        'transaction_multiplier': 1.1,
        'category_spend_multiplier': {
            'payroll': 1.4,
            'operations': 0.95,
            'tech': 1.1,
            'marketing': 0.65,
        },
        'anomaly_category': 'payroll',
    },
}


SCALE_PROFILES = {
    'small_business': {
        'transaction_multiplier': 0.55,
        'spend_multiplier': 0.5,
    },
    'startup': {
        'transaction_multiplier': 0.75,
        'spend_multiplier': 0.65,
    },
    'mid_market': {
        'transaction_multiplier': 1.0,
        'spend_multiplier': 1.0,
    },
    'enterprise': {
        'transaction_multiplier': 1.6,
        'spend_multiplier': 1.75,
    },
    'large_enterprise': {
        'transaction_multiplier': 2.2,
        'spend_multiplier': 2.4,
    },
}

MACRO_PROFILES = {
    'stable': {
        'transaction_multiplier': 1.0,
        'spend_multiplier': 1.0,
        'variance_multiplier': 1.0,
        'anomaly_multiplier': 1.0,
    },
    'inflationary': {
        'transaction_multiplier': 1.05,
        'spend_multiplier': 1.12,
        'variance_multiplier': 1.18,
        'anomaly_multiplier': 1.08,
    },
    'recessionary': {
        'transaction_multiplier': 0.92,
        'spend_multiplier': 0.94,
        'variance_multiplier': 1.1,
        'anomaly_multiplier': 1.15,
    },
}

COUNTRY_PROFILES = {
    'united_states': {'transaction_multiplier': 1.08, 'spend_multiplier': 1.12, 'variance_multiplier': 0.98},
    'india': {'transaction_multiplier': 0.94, 'spend_multiplier': 0.82, 'variance_multiplier': 1.08},
    'singapore': {'transaction_multiplier': 0.9, 'spend_multiplier': 0.96, 'variance_multiplier': 0.94},
    'united_kingdom': {'transaction_multiplier': 1.0, 'spend_multiplier': 1.03, 'variance_multiplier': 0.99},
    'uae': {'transaction_multiplier': 0.93, 'spend_multiplier': 0.98, 'variance_multiplier': 1.03},
    'germany': {'transaction_multiplier': 0.97, 'spend_multiplier': 1.01, 'variance_multiplier': 0.96},
}

FUNDING_ROUND_PROFILES = {
    'bootstrapped': {'transaction_multiplier': 0.72, 'spend_multiplier': 0.76, 'variance_multiplier': 0.92, 'anomaly_multiplier': 0.95},
    'seed': {'transaction_multiplier': 0.86, 'spend_multiplier': 0.88, 'variance_multiplier': 1.0, 'anomaly_multiplier': 1.0},
    'series_a': {'transaction_multiplier': 1.0, 'spend_multiplier': 1.0, 'variance_multiplier': 1.0, 'anomaly_multiplier': 1.0},
    'series_b': {'transaction_multiplier': 1.08, 'spend_multiplier': 1.08, 'variance_multiplier': 1.02, 'anomaly_multiplier': 1.03},
    'series_c': {'transaction_multiplier': 1.16, 'spend_multiplier': 1.15, 'variance_multiplier': 1.04, 'anomaly_multiplier': 1.05},
    'public': {'transaction_multiplier': 1.24, 'spend_multiplier': 1.22, 'variance_multiplier': 0.96, 'anomaly_multiplier': 0.98},
}

STATE_OF_BUSINESS_PROFILES = {
    'survival': {
        'transaction_multiplier': 0.88,
        'spend_multiplier': 0.84,
        'variance_multiplier': 0.96,
        'marketing_multiplier': 0.8,
        'tech_multiplier': 0.92,
    },
    'profit': {
        'transaction_multiplier': 1.0,
        'spend_multiplier': 0.98,
        'variance_multiplier': 0.92,
        'marketing_multiplier': 0.9,
        'tech_multiplier': 0.98,
    },
    'growth': {
        'transaction_multiplier': 1.12,
        'spend_multiplier': 1.14,
        'variance_multiplier': 1.12,
        'marketing_multiplier': 1.22,
        'tech_multiplier': 1.08,
    },
}


def _market_cap_factor(company_market_capital):
    """Convert company market-cap size into a stable scaling factor."""
    normalized = min(max(float(company_market_capital), 50.0), 2000.0)
    return 0.9 + ((normalized - 50.0) / 1950.0) * 0.25


def _company_age_profile(company_age_years):
    """Map company age to transaction, spend, and variance behavior."""
    age = min(max(float(company_age_years), 1.0), 50.0)
    if age <= 3:
        return {
            'transaction_multiplier': 0.82,
            'spend_multiplier': 0.92,
            'variance_multiplier': 1.18,
            'marketing_multiplier': 1.18,
            'operations_multiplier': 0.92,
        }
    if age <= 8:
        return {
            'transaction_multiplier': 0.98,
            'spend_multiplier': 1.0,
            'variance_multiplier': 1.05,
            'marketing_multiplier': 1.08,
            'operations_multiplier': 1.0,
        }
    if age <= 15:
        return {
            'transaction_multiplier': 1.08,
            'spend_multiplier': 1.06,
            'variance_multiplier': 0.96,
            'marketing_multiplier': 0.96,
            'operations_multiplier': 1.08,
        }
    return {
        'transaction_multiplier': 1.14,
        'spend_multiplier': 1.1,
        'variance_multiplier': 0.9,
        'marketing_multiplier': 0.9,
        'operations_multiplier': 1.12,
    }


def _capital_efficiency_profile(capital_efficiency_score):
    """Map capital efficiency to spend discipline and volatility."""
    score = min(max(float(capital_efficiency_score), 0.0), 100.0)
    return {
        'spend_multiplier': 1.12 - (score / 100.0) * 0.24,
        'variance_multiplier': 1.12 - (score / 100.0) * 0.22,
        'tech_multiplier': 1.04 - (score / 100.0) * 0.08,
        'marketing_multiplier': 1.1 - (score / 100.0) * 0.18,
    }


def _scenario_seed(
    days,
    sector,
    business_scale,
    macro_environment,
    country,
    company_market_capital,
    funding_round,
    state_of_business,
    company_age_years,
    capital_efficiency_score,
    seed,
):
    """Build a deterministic seed for the selected business scenario."""
    scenario_key = (
        f"{days}:{sector}:{business_scale}:{macro_environment}:"
        f"{country}:{company_market_capital}:{funding_round}:{state_of_business}:"
        f"{company_age_years}:{capital_efficiency_score}:{seed}"
    )
    digest = hashlib.sha256(scenario_key.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def generate_financial_data(
    days=90,
    sector='saas',
    business_scale='mid_market',
    macro_environment='stable',
    country='united_states',
    company_market_capital=500,
    funding_round='series_a',
    state_of_business='profit',
    company_age_years=5,
    capital_efficiency_score=50,
    seed=42,
):
    """
    Generate 90 days of synthetic transaction data.
    
    Args:
        days: Number of days to generate
        sector: Business sector profile
        business_scale: Business scale profile
        macro_environment: Macro environment profile
        company_age_years: Company age in years
        capital_efficiency_score: Capital efficiency score from 0-100
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame with columns: date, category, amount, vendor
    """
    rng = np.random.default_rng(
        _scenario_seed(
            days,
            sector,
            business_scale,
            macro_environment,
            country,
            company_market_capital,
            funding_round,
            state_of_business,
            company_age_years,
            capital_efficiency_score,
            seed,
        )
    )
    sector_profile = SECTOR_PROFILES.get(sector, SECTOR_PROFILES['saas'])
    scale_profile = SCALE_PROFILES.get(business_scale, SCALE_PROFILES['mid_market'])
    macro_profile = MACRO_PROFILES.get(macro_environment, MACRO_PROFILES['stable'])
    country_profile = COUNTRY_PROFILES.get(country, COUNTRY_PROFILES['united_states'])
    funding_profile = FUNDING_ROUND_PROFILES.get(funding_round, FUNDING_ROUND_PROFILES['series_a'])
    state_profile = STATE_OF_BUSINESS_PROFILES.get(state_of_business, STATE_OF_BUSINESS_PROFILES['profit'])
    market_cap_factor = _market_cap_factor(company_market_capital)
    age_profile = _company_age_profile(company_age_years)
    capital_profile = _capital_efficiency_profile(capital_efficiency_score)
    
    # Define categories and base daily spend distribution
    categories = {
        'payroll': {
            'daily_spend': 5000,
            'variance': 0.05,
            'vendors': ['Payroll System', 'HR Platform']
        },
        'operations': {
            'daily_spend': 2000,
            'variance': 0.15,
            'vendors': ['Office Supplies', 'Utilities', 'Maintenance']
        },
        'tech': {
            'daily_spend': 1500,
            'variance': 0.20,
            'vendors': ['AWS', 'Software License', 'IT Support']
        },
        'marketing': {
            'daily_spend': 1000,
            'variance': 0.25,
            'vendors': ['Ad Network', 'Agency', 'Content Platform']
        }
    }
    
    records = []
    start_date = datetime.now() - timedelta(days=days)
    
    for day in range(days):
        current_date = start_date + timedelta(days=day)
        
        for category, config in categories.items():
            # Transaction count varies by sector and business scale.
            transaction_lambda = (
                2
                * sector_profile['transaction_multiplier']
                * scale_profile['transaction_multiplier']
                * macro_profile['transaction_multiplier']
                * country_profile['transaction_multiplier']
                * funding_profile['transaction_multiplier']
                * state_profile['transaction_multiplier']
                * age_profile['transaction_multiplier']
                * market_cap_factor
            )
            num_transactions = max(1, rng.poisson(transaction_lambda))
            
            for _ in range(num_transactions):
                # Sector-specific anomalies make the generated business feel less generic.
                multiplier = 1.0
                if category == sector_profile['anomaly_category'] and day >= (days - 10):
                    multiplier = (
                        rng.uniform(1.25, 1.45)
                        * macro_profile['anomaly_multiplier']
                        * funding_profile['anomaly_multiplier']
                    )
                
                sector_spend = sector_profile['category_spend_multiplier'].get(category, 1.0)
                age_category_multiplier = (
                    age_profile['marketing_multiplier'] if category == 'marketing'
                    else age_profile['operations_multiplier'] if category == 'operations'
                    else 1.0
                )
                capital_category_multiplier = (
                    capital_profile['tech_multiplier'] if category == 'tech'
                    else capital_profile['marketing_multiplier'] if category == 'marketing'
                    else 1.0
                )
                state_category_multiplier = (
                    state_profile['marketing_multiplier'] if category == 'marketing'
                    else state_profile['tech_multiplier'] if category == 'tech'
                    else 1.0
                )
                amount = (
                    config['daily_spend']
                    * scale_profile['spend_multiplier']
                    * macro_profile['spend_multiplier']
                    * country_profile['spend_multiplier']
                    * funding_profile['spend_multiplier']
                    * state_profile['spend_multiplier']
                    * age_profile['spend_multiplier']
                    * capital_profile['spend_multiplier']
                    * market_cap_factor
                    * sector_spend
                    * age_category_multiplier
                    * capital_category_multiplier
                    * state_category_multiplier
                    * rng.uniform(
                        1 - (
                            config['variance']
                            * macro_profile['variance_multiplier']
                            * country_profile['variance_multiplier']
                            * funding_profile['variance_multiplier']
                            * state_profile['variance_multiplier']
                            * age_profile['variance_multiplier']
                            * capital_profile['variance_multiplier']
                        ),
                        1 + (
                            config['variance']
                            * macro_profile['variance_multiplier']
                            * country_profile['variance_multiplier']
                            * funding_profile['variance_multiplier']
                            * state_profile['variance_multiplier']
                            * age_profile['variance_multiplier']
                            * capital_profile['variance_multiplier']
                        )
                    )
                    * multiplier
                )
                
                vendor = rng.choice(config['vendors'])
                
                records.append({
                    'date': current_date,
                    'category': category,
                    'amount': round(amount, 2),
                    'vendor': vendor
                })
    
    df = pd.DataFrame(records)
    df = df.sort_values('date').reset_index(drop=True)
    
    return df


def get_transaction_data(
    source='synthetic',
    days=90,
    sector='saas',
    business_scale='mid_market',
    macro_environment='stable',
    country='united_states',
    company_market_capital=500,
    funding_round='series_a',
    state_of_business='profit',
    company_age_years=5,
    capital_efficiency_score=50,
    zaggle_export_path=None,
):
    """
    Unified transaction loader.

    Returns:
        (DataFrame, metadata)
    """
    if source == 'zaggle':
        try:
            df = load_zaggle_transactions(export_path=zaggle_export_path)
            if len(df) == 0:
                raise ValueError("Zaggle export is empty.")
            return df.sort_values('date').reset_index(drop=True), {
                'data_source': 'zaggle',
                'data_source_status': 'connected',
                'data_source_message': (
                    f"Loaded Zaggle-style transactions from "
                    f"{zaggle_export_path or os.getenv('ZAGGLE_EXPORT_PATH', 'configured source')}."
                ),
            }
        except Exception as exc:
            df = generate_financial_data(
                days=days,
                sector=sector,
                business_scale=business_scale,
                macro_environment=macro_environment,
                country=country,
                company_market_capital=company_market_capital,
                funding_round=funding_round,
                state_of_business=state_of_business,
                company_age_years=company_age_years,
                capital_efficiency_score=capital_efficiency_score,
            )
            return df, {
                'data_source': 'zaggle',
                'data_source_status': 'fallback_synthetic',
                'data_source_message': f"Zaggle source unavailable. Falling back to synthetic data: {exc}",
            }

    df = generate_financial_data(
        days=days,
        sector=sector,
        business_scale=business_scale,
        macro_environment=macro_environment,
        country=country,
        company_market_capital=company_market_capital,
        funding_round=funding_round,
        state_of_business=state_of_business,
        company_age_years=company_age_years,
        capital_efficiency_score=capital_efficiency_score,
    )
    return df, {
        'data_source': 'synthetic',
        'data_source_status': 'connected',
        'data_source_message': 'Using the built-in synthetic transaction generator.',
    }


def get_budget_config():
    """
    Get monthly budget configuration per category.
    
    Returns:
        Dict with category budgets
    """
    return {
        'payroll': 150000,      # ~5000/day
        'operations': 60000,    # ~2000/day
        'tech': 45000,          # ~1500/day
        'marketing': 30000      # ~1000/day
    }


def get_upcoming_payments(
    sector='saas',
    business_scale='mid_market',
    macro_environment='stable',
    close_pressure='medium',
    country='united_states',
    company_market_capital=500,
    funding_round='series_a',
    state_of_business='profit',
    company_age_years=5,
    capital_efficiency_score=50,
    seed=42,
):
    """
    Get upcoming vendor payments for next 30 days.
    
    Returns:
        List of dicts with date, vendor, and amount
    """
    now = datetime.now().date()
    rng = np.random.default_rng(
        _scenario_seed(
            30,
            sector,
            business_scale,
            f"{macro_environment}:{close_pressure}",
            country,
            company_market_capital,
            funding_round,
            state_of_business,
            company_age_years,
            capital_efficiency_score,
            seed + 7,
        )
    )
    sector_profile = SECTOR_PROFILES.get(sector, SECTOR_PROFILES['saas'])
    scale_profile = SCALE_PROFILES.get(business_scale, SCALE_PROFILES['mid_market'])
    macro_profile = MACRO_PROFILES.get(macro_environment, MACRO_PROFILES['stable'])
    country_profile = COUNTRY_PROFILES.get(country, COUNTRY_PROFILES['united_states'])
    funding_profile = FUNDING_ROUND_PROFILES.get(funding_round, FUNDING_ROUND_PROFILES['series_a'])
    state_profile = STATE_OF_BUSINESS_PROFILES.get(state_of_business, STATE_OF_BUSINESS_PROFILES['profit'])
    market_cap_factor = _market_cap_factor(company_market_capital)
    age_profile = _company_age_profile(company_age_years)
    capital_profile = _capital_efficiency_profile(capital_efficiency_score)
    close_pressure_profile = {
        'low': {'queue_multiplier': 0.85, 'amount_multiplier': 0.95, 'base_extra_payments': 0},
        'medium': {'queue_multiplier': 1.0, 'amount_multiplier': 1.0, 'base_extra_payments': 1},
        'high': {'queue_multiplier': 1.25, 'amount_multiplier': 1.1, 'base_extra_payments': 2},
        'quarter_end': {'queue_multiplier': 1.5, 'amount_multiplier': 1.18, 'base_extra_payments': 4},
    }.get(close_pressure, {'queue_multiplier': 1.0, 'amount_multiplier': 1.0})

    base_templates = [
        {'day': 3, 'vendor': 'AWS', 'amount': 15000, 'category': 'tech'},
        {'day': 7, 'vendor': 'Payroll System', 'amount': 50000, 'category': 'payroll'},
        {'day': 10, 'vendor': 'Software License', 'amount': 8000, 'category': 'tech'},
        {'day': 15, 'vendor': 'Agency', 'amount': 12000, 'category': 'marketing'},
        {'day': 20, 'vendor': 'Utilities', 'amount': 5000, 'category': 'operations'},
        {'day': 25, 'vendor': 'Payroll System', 'amount': 50000, 'category': 'payroll'},
    ]

    payments = []
    for template in base_templates:
        category_multiplier = sector_profile['category_spend_multiplier'].get(template['category'], 1.0)
        amount = (
            template['amount']
            * scale_profile['spend_multiplier']
            * macro_profile['spend_multiplier']
            * country_profile['spend_multiplier']
            * funding_profile['spend_multiplier']
            * state_profile['spend_multiplier']
            * age_profile['spend_multiplier']
            * capital_profile['spend_multiplier']
            * market_cap_factor
            * close_pressure_profile['amount_multiplier']
            * category_multiplier
            * rng.uniform(0.9, 1.1)
        )
        payments.append({
            'date': now + timedelta(days=template['day']),
            'vendor': template['vendor'],
            'amount': round(amount, 2),
            'category': template['category'],
        })

    # Larger businesses and inflationary environments create denser close queues.
    extra_payment_count = max(
        0,
        int(round(
            (
                ((scale_profile['transaction_multiplier'] - 1.0) * 3)
                + ((macro_profile['transaction_multiplier'] - 1.0) * 5)
                + ((country_profile['transaction_multiplier'] - 1.0) * 4)
                + ((funding_profile['transaction_multiplier'] - 1.0) * 4)
                + ((state_profile['transaction_multiplier'] - 1.0) * 4)
                + ((age_profile['transaction_multiplier'] - 1.0) * 3)
            )
            * close_pressure_profile['queue_multiplier']
        )) + close_pressure_profile['base_extra_payments']
    )
    categories = list(sector_profile['category_spend_multiplier'].keys())
    vendor_map = {
        'payroll': ['Payroll System', 'Benefits Admin'],
        'operations': ['Utilities', 'Maintenance', 'Office Supplies'],
        'tech': ['AWS', 'Software License', 'IT Support'],
        'marketing': ['Agency', 'Ad Network', 'Content Platform'],
    }
    for _ in range(extra_payment_count):
        category = rng.choice(categories)
        payments.append({
            'date': now + timedelta(days=int(rng.integers(4, 29))),
            'vendor': rng.choice(vendor_map[category]),
            'amount': round(
                6000
                * scale_profile['spend_multiplier']
                * macro_profile['spend_multiplier']
                * country_profile['spend_multiplier']
                * funding_profile['spend_multiplier']
                * state_profile['spend_multiplier']
                * age_profile['spend_multiplier']
                * capital_profile['spend_multiplier']
                * market_cap_factor
                * close_pressure_profile['amount_multiplier']
                * sector_profile['category_spend_multiplier'].get(category, 1.0)
                * rng.uniform(0.8, 1.6),
                2,
            ),
            'category': category,
        })

    payments.sort(key=lambda item: (item['date'], item['amount']))
    return payments


if __name__ == '__main__':
    df = generate_financial_data()
    print(f"Generated {len(df)} transactions")
    print(df.head(10))
    print(f"\nCategories: {df['category'].unique()}")
    print(f"\nDate range: {df['date'].min()} to {df['date'].max()}")
