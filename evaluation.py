"""
Evaluation Module
Track system performance and decision accuracy.
"""
from datetime import datetime


class CFOEvaluator:
    """Evaluate system performance and accuracy."""
    
    def __init__(self):
        self.anomaly_detections = []
        self.forecast_accuracy = []
        self.decision_outcomes = []
    
    def record_anomaly_detection(self, category, detected, actual, confidence):
        """
        Record anomaly detection result.
        
        Args:
            category: Category name
            detected: Whether anomaly was detected
            actual: Whether anomaly actually occurred
            confidence: Detection confidence score
        """
        record = {
            'timestamp': datetime.now().isoformat(),
            'category': category,
            'detected': detected,
            'actual': actual,
            'confidence': confidence,
            'correct': detected == actual,
        }
        self.anomaly_detections.append(record)
    
    def record_forecast(self, forecast_value, actual_value, days_ahead):
        """
        Record forecast accuracy.
        
        Args:
            forecast_value: Predicted value
            actual_value: Actual value observed
            days_ahead: How many days ahead was this forecast
        """
        if actual_value == 0:
            mape = 0
        else:
            mape = abs((actual_value - forecast_value) / actual_value) * 100
        
        record = {
            'timestamp': datetime.now().isoformat(),
            'forecast': forecast_value,
            'actual': actual_value,
            'mape': mape,
            'days_ahead': days_ahead,
        }
        self.forecast_accuracy.append(record)
    
    def record_decision_outcome(self, decision_id, action, intended_risk_reduction, actual_outcome):
        """
        Record decision outcome for learning.
        
        Args:
            decision_id: Unique decision identifier
            action: Action taken
            intended_risk_reduction: Expected risk reduction
            actual_outcome: What actually happened
        """
        record = {
            'timestamp': datetime.now().isoformat(),
            'decision_id': decision_id,
            'action': action,
            'intended_risk_reduction': intended_risk_reduction,
            'actual_outcome': actual_outcome,
            'effective': actual_outcome >= (intended_risk_reduction * 0.8),  # 80% threshold
        }
        self.decision_outcomes.append(record)
    
    def get_anomaly_metrics(self):
        """
        Get anomaly detection metrics (precision, recall).
        
        Returns:
            Dict with metrics
        """
        if not self.anomaly_detections:
            return None
        
        tp = sum(1 for r in self.anomaly_detections if r['correct'] and r['detected'])
        fp = sum(1 for r in self.anomaly_detections if not r['correct'] and r['detected'])
        fn = sum(1 for r in self.anomaly_detections if not r['correct'] and not r['detected'])
        tn = sum(1 for r in self.anomaly_detections if r['correct'] and not r['detected'])
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        accuracy = (tp + tn) / len(self.anomaly_detections) if self.anomaly_detections else 0
        
        return {
            'precision': precision,
            'recall': recall,
            'accuracy': accuracy,
            'true_positives': tp,
            'false_positives': fp,
            'false_negatives': fn,
            'true_negatives': tn,
        }
    
    def get_forecast_metrics(self):
        """
        Get forecast accuracy metrics.
        
        Returns:
            Dict with MAPE and other metrics
        """
        if not self.forecast_accuracy:
            return None
        
        recent = self.forecast_accuracy[-20:]  # Last 20 forecasts
        mape_values = [r['mape'] for r in recent]
        
        return {
            'mean_absolute_percentage_error': sum(mape_values) / len(mape_values),
            'median_mape': sorted(mape_values)[len(mape_values) // 2],
            'best_mape': min(mape_values),
            'worst_mape': max(mape_values),
            'forecast_count': len(self.forecast_accuracy),
        }
    
    def get_decision_effectiveness(self):
        """
        Get decision making effectiveness.
        
        Returns:
            Dict with effectiveness metrics
        """
        if not self.decision_outcomes:
            return None
        
        effective_count = sum(1 for r in self.decision_outcomes if r['effective'])
        total = len(self.decision_outcomes)
        
        return {
            'total_decisions': total,
            'effective_decisions': effective_count,
            'effectiveness_rate': effective_count / total if total > 0 else 0,
        }
    
    def get_overall_report(self):
        """
        Get overall system performance report.
        
        Returns:
            Dict with all metrics
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'anomaly_metrics': self.get_anomaly_metrics(),
            'forecast_metrics': self.get_forecast_metrics(),
            'decision_metrics': self.get_decision_effectiveness(),
        }


# Global evaluator instance
evaluator = CFOEvaluator()


if __name__ == '__main__':
    eval_system = CFOEvaluator()
    
    # Test recording
    eval_system.record_anomaly_detection('marketing', True, True, 0.92)
    eval_system.record_forecast(10000, 9800, 1)
    eval_system.record_decision_outcome('dec_001', 'cut_marketing', 0.3, 0.28)
    
    print("Anomaly Metrics:", eval_system.get_anomaly_metrics())
    print("Forecast Metrics:", eval_system.get_forecast_metrics())
    print("Decision Effectiveness:", eval_system.get_decision_effectiveness())
