import numpy as np
from datetime import datetime, timedelta

class AnomalyDetector:
    """
    Advanced anomaly detection for conversation memory and dataset loads.
    Supports thresholding, time-window analysis, and statistical outlier detection.
    """
    def __init__(self, window_minutes=10, load_threshold=3, z_thresh=2.5):
        self.window_minutes = window_minutes
        self.load_threshold = load_threshold
        self.z_thresh = z_thresh

    def detect_repeated_loads(self, load_events):
        """
        Detects if a dataset is loaded more than 'load_threshold' times in a rolling time window.
        load_events: list of dicts with 'timestamp' (ISO8601)
        """
        now = datetime.now()
        window_start = now - timedelta(minutes=self.window_minutes)
        count = sum(1 for e in load_events if datetime.fromisoformat(e['timestamp']) >= window_start)
        return count >= self.load_threshold

    def detect_statistical_anomaly(self, all_counts):
        """
        Detects if the latest count is a statistical outlier (z-score based).
        all_counts: list of int (e.g., loads per hour)
        """
        if len(all_counts) < 5:
            return False
        mean = np.mean(all_counts[:-1])
        std = np.std(all_counts[:-1])
        if std == 0:
            return False
        z = abs((all_counts[-1] - mean) / std)
        return z > self.z_thresh
