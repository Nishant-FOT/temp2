"""
Spend Intelligence Agent
Detects and analyzes spending anomalies.
"""
from inference import detect_anomalies, detect_anomalies_zscore


class SpendIntelligenceAgent:
    """Detect and analyze spending anomalies."""
    
    def __init__(self, name="SpendIntelligenceAgent"):
        self.name = name
    
    def analyze(self, features, budget_config):
        """
        Analyze spending patterns and detect anomalies.
        
        Args:
            features: Features dict from feature engineering
            budget_config: Budget configuration
            
        Returns:
            Dict with anomaly analysis
        """
        # Get anomaly scores
        anomaly_scores = detect_anomalies(features)
        
        # Find largest anomaly
        if not anomaly_scores:
            return self._no_anomaly_result()
        
        max_category = max(anomaly_scores, key=anomaly_scores.get)
        max_score = anomaly_scores[max_category]
        
        # Calculate percent change for this category
        growth_pct = features['category_growth'].get(max_category, 0)
        
        # Determine severity
        severity = self._classify_severity(max_score, growth_pct)
        budget_consumption = features.get('budget_consumption_rate', {}).get(max_category, 0)
        vendor_concentration = features.get('vendor_concentration', {}).get(max_category, {})
        hhi = vendor_concentration.get('hhi', 0)
        top_vendor = vendor_concentration.get('top_vendor', 'n/a')
        top_vendor_share = vendor_concentration.get('top_vendor_share', 0)
        
        # Build reason
        if max_score > 0.7:
            reason = (
                f"Detected unusual spending pattern. {max_category.title()} spending increased by "
                f"{abs(growth_pct):.1f}% in the last 7 days, budget consumption is at {budget_consumption:.0%}, "
                f"and vendor concentration is {hhi:.2f} HHI."
            )
        else:
            reason = (
                f"Minor spending variance detected in {max_category.title()}, with budget consumption at "
                f"{budget_consumption:.0%} and top vendor share at {top_vendor_share:.0%}."
            )
        
        return {
            'issue': f"Spending anomaly detected in {max_category}",
            'category': max_category,
            'percent_change': growth_pct,
            'severity': severity,
            'reason': reason,
            'confidence': min(1.0, max_score),
            'anomaly_scores': anomaly_scores,
            'budget_consumption_rate': features.get('budget_consumption_rate', {}),
            'vendor_concentration': features.get('vendor_concentration', {}),
            'headline_budget_consumption': round(budget_consumption, 4),
            'headline_vendor_hhi': round(hhi, 4),
            'headline_top_vendor': top_vendor,
            'headline_top_vendor_share': round(top_vendor_share, 4),
        }
    
    def _classify_severity(self, anomaly_score, percent_change):
        """Classify severity based on anomaly score and percent change."""
        if anomaly_score > 0.8 and abs(percent_change) > 25:
            return 'critical'
        elif anomaly_score > 0.6 and abs(percent_change) > 20:
            return 'high'
        elif anomaly_score > 0.4 and abs(percent_change) > 15:
            return 'medium'
        else:
            return 'low'
    
    def _no_anomaly_result(self):
        """Return result when no anomalies detected."""
        return {
            'issue': 'No significant anomalies detected',
            'category': None,
            'percent_change': 0,
            'severity': 'low',
            'reason': 'All spending categories within expected ranges.',
            'confidence': 0.95,
            'anomaly_scores': {},
            'budget_consumption_rate': {},
            'vendor_concentration': {},
            'headline_budget_consumption': 0.0,
            'headline_vendor_hhi': 0.0,
            'headline_top_vendor': 'n/a',
            'headline_top_vendor_share': 0.0,
        }
    
    def get_context(self):
        """Get agent context for orchestrator."""
        return {
            'name': self.name,
            'role': 'Spend Intelligence',
            'responsibility': 'Detect and analyze spending anomalies',
        }


if __name__ == '__main__':
    from data import generate_financial_data, get_budget_config
    from features import build_features
    
    df = generate_financial_data()
    budget_config = get_budget_config()
    features = build_features(df, budget_config)
    
    agent = SpendIntelligenceAgent()
    result = agent.analyze(features, budget_config)
    
    print("Spend Intelligence Analysis:")
    print(f"  Issue: {result['issue']}")
    print(f"  Category: {result['category']}")
    print(f"  Percent Change: {result['percent_change']:.2f}%")
    print(f"  Severity: {result['severity']}")
    print(f"  Confidence: {result['confidence']:.2f}")
