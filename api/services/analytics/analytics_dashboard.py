import matplotlib.pyplot as plt
from collections import Counter

class AnalyticsDashboard:
    """
    Provides visualization and summary analytics for conversation memory.
    """
    def plot_message_volume(self, conversations):
        counts = [len(c['messages']) for c in conversations.values()]
        plt.hist(counts, bins=10)
        plt.title('Message Volume per Conversation')
        plt.xlabel('Messages')
        plt.ylabel('Conversations')
        plt.show()

    def plot_user_activity(self, conversations):
        user_counts = Counter([c['user_id'] for c in conversations.values() if c.get('user_id')])
        plt.bar(user_counts.keys(), user_counts.values())
        plt.title('User Activity')
        plt.xlabel('User ID')
        plt.ylabel('Conversations')
        plt.show()

    def plot_anomalies(self, anomaly_log):
        if not anomaly_log:
            print('No anomalies detected.')
            return
        times = [a['timestamp'] for a in anomaly_log]
        plt.hist(times, bins=10)
        plt.title('Anomaly Events Over Time')
        plt.xlabel('Timestamp')
        plt.ylabel('Anomaly Count')
        plt.show()

    # === ADVANCED ANALYTICS METHODS ===
    def conversation_length_histogram(self, conversations):
        """Returns list of bins: [{"bin": "1-5", "count": 12}, ...]"""
        def _bin(length):
            if length <= 5: return "1-5"
            elif length <= 10: return "6-10"
            elif length <= 20: return "11-20"
            else: return "21+"
        bins = [_bin(len(conv.get('messages', []))) for conv in conversations.values()]
        counts = Counter(bins)
        return [{"bin": b, "count": counts[b]} for b in sorted(counts.keys())]

    def cohort_retention(self, conversations):
        """Cohort by first message date (YYYY-MM), retention = % active each subsequent month."""
        from collections import defaultdict
        from datetime import datetime
        cohorts = defaultdict(list)
        for conv in conversations.values():
            if not conv.get('messages'): continue
            first = conv['messages'][0]
            dt = datetime.fromisoformat(first['timestamp']).strftime('%Y-%m')
            cohorts[dt].append(conv)
        periods = sorted(cohorts.keys())
        result = []
        for cohort, convs in cohorts.items():
            retention = []
            base_users = set(c['user_id'] for c in convs if c.get('user_id'))
            for period in periods:
                users = set(c['user_id'] for c in cohorts[period] if c.get('user_id'))
                retained = len(base_users & users) / len(base_users) * 100 if base_users else 0
                retention.append(retained)
            result.append({"cohort": cohort, "retention": retention})
        return {"cohorts": result, "periods": periods}

    def first_response_time(self, conversations):
        """Returns {"avgTime": seconds, "medianTime": seconds}"""
        from datetime import datetime
        times = []
        for conv in conversations.values():
            msgs = conv.get('messages', [])
            if len(msgs) < 2: continue
            user_msg = next((m for m in msgs if m['sender'] == 'user'), None)
            bot_msg = next((m for m in msgs if m['sender'] == 'bot' and m['timestamp'] > user_msg['timestamp']), None) if user_msg else None
            if user_msg and bot_msg:
                t1 = datetime.fromisoformat(user_msg['timestamp'])
                t2 = datetime.fromisoformat(bot_msg['timestamp'])
                times.append((t2 - t1).total_seconds())
        if not times:
            return {"avgTime": 0, "medianTime": 0}
        try:
            import numpy as np
            avg = float(np.mean(times))
            median = float(np.median(times))
        except ImportError:
            times.sort()
            avg = sum(times) / len(times)
            n = len(times)
            median = times[n//2] if n % 2 == 1 else (times[n//2 - 1] + times[n//2]) / 2
        return {"avgTime": avg, "medianTime": median}

    def funnel_analysis(self, conversations):
        """Example: stages = started, engaged (>=3 msgs), completed (has evaluation)"""
        stages = {"Started": 0, "Engaged": 0, "Completed": 0}
        for conv in conversations.values():
            stages["Started"] += 1
            if len(conv.get('messages', [])) >= 3:
                stages["Engaged"] += 1
            if conv.get('evaluations'):
                stages["Completed"] += 1
        return [{"name": k, "value": v} for k, v in stages.items()]

    def user_segmentation(self, conversations):
        """Segment by user type if present, else by user_id prefix."""
        segments = Counter()
        for conv in conversations.values():
            user = conv.get('user_id', 'unknown')
            # Example: segment by prefix or type
            if isinstance(user, str) and user.startswith('admin'):
                segment = 'admin'
            elif isinstance(user, str) and user.startswith('guest'):
                segment = 'guest'
            else:
                segment = 'user'
            segments[segment] += 1
        return [{"segment": k, "count": v} for k, v in segments.items()]
