"""
Memory Module
Store and retrieve past anomalies and decisions.
"""
from datetime import datetime
import json


class CFOMemory:
    """In-memory storage for anomalies and decisions."""
    
    def __init__(self):
        self.anomalies = []
        self.decisions = []
        self.max_history = 100
    
    def record_anomaly(self, category, severity, percent_change, reason):
        """
        Record a detected anomaly.
        
        Args:
            category: Category name
            severity: 'low', 'medium', 'high', 'critical'
            percent_change: Percentage change
            reason: Description of anomaly
        """
        record = {
            'timestamp': datetime.now().isoformat(),
            'category': category,
            'severity': severity,
            'percent_change': percent_change,
            'reason': reason,
        }
        self.anomalies.append(record)
        
        # Keep memory bounded
        if len(self.anomalies) > self.max_history:
            self.anomalies = self.anomalies[-self.max_history:]
    
    def record_decision(self, action, risk_score, confidence, context):
        """
        Record a decision made by the system.
        
        Args:
            action: Recommended action
            risk_score: Risk score of chosen action
            confidence: Confidence in decision
            context: Decision context/rationale
        """
        record = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'risk_score': risk_score,
            'confidence': confidence,
            'context': context,
        }
        self.decisions.append(record)
        
        # Keep memory bounded
        if len(self.decisions) > self.max_history:
            self.decisions = self.decisions[-self.max_history:]
    
    def get_last_decision(self):
        """Get the most recent decision."""
        if self.decisions:
            return self.decisions[-1]
        return None
    
    def get_last_anomalies(self, count=5):
        """Get the last N anomalies."""
        return self.anomalies[-count:]
    
    def get_anomaly_count(self, hours=24):
        """Get count of anomalies in the last N hours."""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(hours=hours)
        count = 0
        for record in self.anomalies:
            ts = datetime.fromisoformat(record['timestamp'])
            if ts > cutoff:
                count += 1
        return count
    
    def get_decision_history(self, count=10):
        """Get decision history."""
        return self.decisions[-count:]
    
    def get_pattern_summary(self):
        """Get summary of patterns in decision history."""
        if not self.decisions:
            return None
        
        recent = self.decisions[-10:]
        action_counts = {}
        total_confidence = 0
        
        for decision in recent:
            action = decision['action']
            action_counts[action] = action_counts.get(action, 0) + 1
            total_confidence += decision['confidence']
        
        return {
            'recent_decisions': len(recent),
            'most_common_action': max(action_counts, key=lambda a: action_counts[a]) if action_counts else None,
            'average_confidence': total_confidence / len(recent) if recent else 0,
        }


# Global memory instance
memory = CFOMemory()


if __name__ == '__main__':
    mem = CFOMemory()
    
    # Test recording
    mem.record_anomaly('marketing', 'high', 35, 'Unusual spike in ad spend')
    mem.record_decision('cut_marketing', 0.4, 0.85, 'Reduce ad spend by 20%')
    
    print("Last decision:", mem.get_last_decision())
    print("Anomaly count (24h):", mem.get_anomaly_count(24))
    print("Pattern summary:", mem.get_pattern_summary())
