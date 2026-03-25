"""
Feature Engineering Module
Transform raw transaction data into ML-ready features.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def build_features(df, budget_config):
    """
    Build comprehensive features from transaction data.
    
    Args:
        df: Transaction DataFrame
        budget_config: Dict with category budgets
        
    Returns:
        Dict with feature arrays and metadata
    """
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M')
    
    # Daily category spending
    daily_spend = df.groupby(['date', 'category'])['amount'].sum().unstack(fill_value=0)
    
    # Features dictionary to return
    features = {
        'dates': daily_spend.index.tolist(),
        'categories': daily_spend.columns.tolist(),
        'daily_spend_by_category': daily_spend,
    }
    
    # 1. 7-day rolling spend per category
    rolling_7day = daily_spend.rolling(window=7, min_periods=1).sum()
    for cat in rolling_7day.columns:
        features[f'rolling_7day_{cat}'] = rolling_7day[cat].values
    
    # 2. Month-to-date spend vs budget
    current_month_start = datetime.now().replace(day=1)
    month_data = df[df['date'] >= current_month_start]
    mtd_spend = month_data.groupby('category')['amount'].sum()
    
    features['mtd_spend'] = {}
    features['budget_remaining'] = {}
    features['budget_consumption_rate'] = {}
    for cat, budget in budget_config.items():
        spend = float(mtd_spend.get(cat, 0))
        features['mtd_spend'][cat] = spend
        features['budget_remaining'][cat] = float(max(0, budget - spend))
        features['budget_consumption_rate'][cat] = float((spend / budget) if budget else 0)
    
    # 3. Daily burn rate (7-day rolling average)
    daily_total = daily_spend.sum(axis=1)
    burn_rate = daily_total.rolling(window=7, min_periods=1).mean()
    features['burn_rate'] = burn_rate.to_numpy(dtype=float)
    
    # 4. Category growth percentage (compare last 7 days vs previous 7 days)
    features['category_growth'] = {}
    for i, cat in enumerate(daily_spend.columns):
        if len(daily_spend) >= 14:
            prev_7day_avg = daily_spend[cat].iloc[-14:-7].mean()
            current_7day_avg = daily_spend[cat].iloc[-7:].mean()
            if prev_7day_avg > 0:
                growth = ((current_7day_avg - prev_7day_avg) / prev_7day_avg) * 100
            else:
                growth = 0.0
            features['category_growth'][cat] = float(growth)
        else:
            features['category_growth'][cat] = 0.0
    
    # 5. Latest day totals by category
    if len(daily_spend) > 0:
        features['latest_day_spend'] = daily_spend.iloc[-1].to_dict()

    # 6. Vendor concentration metrics by category using HHI
    features['vendor_concentration'] = {}
    for cat in daily_spend.columns:
        category_df = df[df['category'] == cat]
        vendor_totals = category_df.groupby('vendor')['amount'].sum()
        total_vendor_spend = float(vendor_totals.sum())
        if total_vendor_spend > 0:
            vendor_shares = vendor_totals / total_vendor_spend
            hhi = float((vendor_shares ** 2).sum())
            top_vendor = str(vendor_totals.idxmax())
            top_vendor_share = float(vendor_totals.max() / total_vendor_spend)
        else:
            hhi = 0.0
            top_vendor = 'n/a'
            top_vendor_share = 0.0

        if hhi >= 0.25:
            concentration_level = 'high'
        elif hhi >= 0.15:
            concentration_level = 'medium'
        else:
            concentration_level = 'low'

        features['vendor_concentration'][cat] = {
            'hhi': round(hhi, 4),
            'top_vendor': top_vendor,
            'top_vendor_share': round(top_vendor_share, 4),
            'vendor_count': int(len(vendor_totals)),
            'concentration_level': concentration_level,
        }

    # 7. Total outstanding (upcoming payments)
    features['total_outstanding'] = 0
    
    return features


def get_feature_summary(features):
    """
    Get a human-readable summary of features.
    
    Args:
        features: Features dict
        
    Returns:
        Dict with summary stats
    """
    summary = {
        'total_categories': len(features['categories']),
        'date_range': {
            'start': features['dates'][0] if features['dates'] else None,
            'end': features['dates'][-1] if features['dates'] else None,
        },
        'mtd_spend_total': float(sum(features['mtd_spend'].values())),
        'budget_remaining_total': float(sum(features['budget_remaining'].values())),
        'current_burn_rate': float(features['burn_rate'][-1]) if len(features['burn_rate']) > 0 else 0.0,
    }
    
    return summary


if __name__ == '__main__':
    from data import generate_financial_data, get_budget_config
    
    df = generate_financial_data()
    budget_config = get_budget_config()
    features = build_features(df, budget_config)
    
    print("Features built successfully")
    print(f"Categories: {features['categories']}")
    print(f"\nCategory growth:")
    for cat, growth in features['category_growth'].items():
        print(f"  {cat}: {growth:.2f}%")
    print(f"\nMTD Spend: {features['mtd_spend']}")
    print(f"Budget Remaining: {features['budget_remaining']}")
