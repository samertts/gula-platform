import time
import logging
from decimal import Decimal
from typing import Dict, List

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [PREDICTIVE] - %(levelname)s - %(message)s')
logger = logging.getLogger("gula.predictive")

class GulaPredictiveAnalyzer:
    """
    Analyzes consumption patterns to predict system failures before they occur.
    Implements simple linear trend analysis for disk and memory.
    """
    
    # Thresholds
    DISK_CRITICAL_THRESHOLD = 90.0  # %
    MEM_CRITICAL_THRESHOLD = 85.0   # %
    DB_LATENCY_THRESHOLD = 500      # ms
    
    def __init__(self):
        self.history = {
            "disk_usage": [],
            "mem_usage": [],
            "db_latency": []
        }
        self.max_history = 24  # Keep last 24 hours of data (hourly samples)

    def record_sample(self, disk: float, mem: float, db_lat: float):
        """Records a new system metric sample."""
        self.history["disk_usage"].append(disk)
        self.history["mem_usage"].append(mem)
        self.history["db_latency"].append(db_lat)
        
        # Trim history
        for key in self.history:
            if len(self.history[key]) > self.max_history:
                self.history[key].pop(0)

    def predict_failure(self) -> List[Dict]:
        """
        Analyzes trends and predicts failures within the next 24-48 hours.
        Returns a list of predicted risks.
        """
        risks = []
        
        # 1. Disk Exhaustion Prediction
        if len(self.history["disk_usage"]) >= 3:
            trend = self.history["disk_usage"][-1] - self.history["disk_usage"][0]
            if trend > 0:
                hours_to_critical = (self.DISK_CRITICAL_THRESHOLD - self.history["disk_usage"][-1]) / (trend / len(self.history["disk_usage"]))
                if hours_to_critical < 48:
                    risks.append({
                        "type": "DISK_EXHAUSTION",
                        "severity": "HIGH" if hours_to_critical < 24 else "MEDIUM",
                        "eta_hours": round(hours_to_critical, 1),
                        "message": f"Disk predicted to reach {self.DISK_CRITICAL_THRESHOLD}% in {round(hours_to_critical, 1)} hours."
                    })

        # 2. Memory Leak Detection
        if len(self.history["mem_usage"]) >= 6:
            # Check for consistent upward trend
            upward = all(self.history["mem_usage"][i] < self.history["mem_usage"][i+1] for i in range(len(self.history["mem_usage"])-1))
            if upward:
                risks.append({
                    "type": "MEMORY_LEAK_DETECTED",
                    "severity": "MEDIUM",
                    "message": "Consistent upward memory trend detected. Possible slow leak in backend process."
                })

        # 3. DB Performance Degradation
        if len(self.history["db_latency"]) >= 3:
            avg_lat = sum(self.history["db_latency"]) / len(self.history["db_latency"])
            if avg_lat > self.DB_LATENCY_THRESHOLD * 0.7:
                risks.append({
                    "type": "DB_PERFORMANCE_DEGRADATION",
                    "severity": "LOW",
                    "message": f"Average DB latency ({round(avg_lat)}ms) is approaching threshold."
                })

        return risks

    def run_check(self):
        """Main execution loop for the analyzer."""
        logger.info("Starting predictive analysis cycle...")
        # In a real system, we would fetch metrics from Prometheus or OS
        # For this demonstration, we simulate recording a sample
        # self.record_sample(current_disk, current_mem, current_db_lat)
        
        predictions = self.predict_failure()
        if not predictions:
            logger.info("No immediate risks predicted. System stable.")
        else:
            for risk in predictions:
                logger.warning(f"PREDICTED RISK: {risk['type']} | Severity: {risk['severity']} | {risk['message']}")

if __name__ == "__main__":
    analyzer = GulaPredictiveAnalyzer()
    # Simulate some data points
    analyzer.record_sample(70.0, 40.0, 100.0)
    analyzer.record_sample(72.0, 42.0, 110.0)
    analyzer.record_sample(74.0, 44.0, 120.0)
    analyzer.run_check()
