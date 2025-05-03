from collections import Counter
from typing import List, Dict

class FeedbackAnalytics:
    """
    Provides analytics on user feedback and evaluation patterns.
    """
    def feedback_summary(self, evaluations: List[Dict]) -> Dict:
        categories = Counter()
        ratings = []
        for eval in evaluations:
            if 'category' in eval:
                categories[eval['category']] += 1
            if 'rating' in eval:
                ratings.append(eval['rating'])
        avg_rating = sum(ratings) / len(ratings) if ratings else None
        return {
            'total_evaluations': len(evaluations),
            'category_counts': dict(categories),
            'average_rating': avg_rating
        }

    def most_common_feedback(self, evaluations: List[Dict], n=3) -> List[str]:
        feedbacks = Counter([eval.get('feedback') for eval in evaluations if eval.get('feedback')])
        return [item for item, _ in feedbacks.most_common(n)]

    def feedback_ratings_histogram(self, evaluations: List[Dict]) -> dict:
        """Return histogram of feedback ratings."""
        from collections import Counter
        ratings = [eval.get('rating') for eval in evaluations if 'rating' in eval]
        return dict(Counter(ratings))
