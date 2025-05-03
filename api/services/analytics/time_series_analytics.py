from datetime import datetime
from collections import defaultdict
import matplotlib.pyplot as plt

class TimeSeriesAnalytics:
    """
    Provides time series analytics for conversations, messages, and evaluations.
    """
    def active_users_over_time(self, conversations, freq='D'):
        """Return a dict: {date: unique_active_users} by day or hour."""
        users_by_date = defaultdict(set)
        for conv in conversations.values():
            for msg in conv.get('messages', []):
                ts = datetime.fromisoformat(msg['timestamp'])
                key = ts.strftime('%Y-%m-%d') if freq == 'D' else ts.strftime('%Y-%m-%d %H')
                if 'user_id' in conv:
                    users_by_date[key].add(conv['user_id'])
        return {k: len(v) for k, v in sorted(users_by_date.items())}

    def message_volume_over_time(self, conversations, freq='D'):
        # freq: 'D' = day, 'H' = hour
        time_buckets = defaultdict(int)
        for c in conversations.values():
            for msg in c.get('messages', []):
                ts = msg.get('timestamp')
                if ts:
                    dt = datetime.fromisoformat(ts)
                    bucket = dt.strftime('%Y-%m-%d') if freq == 'D' else dt.strftime('%Y-%m-%d %H')
                    time_buckets[bucket] += 1
        return dict(time_buckets)

    def plot_message_volume_over_time(self, conversations, freq='D'):
        buckets = self.message_volume_over_time(conversations, freq)
        keys = sorted(buckets.keys())
        values = [buckets[k] for k in keys]
        plt.plot(keys, values)
        plt.xticks(rotation=45)
        plt.title('Message Volume Over Time')
        plt.xlabel('Time')
        plt.ylabel('Messages')
        plt.tight_layout()
        plt.show()
