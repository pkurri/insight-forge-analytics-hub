# OpenEvals Integration Guide

This document explains how to utilize OpenEvals in your application for AI response evaluation, improvement, and user feedback—especially when generating business rules, evaluating runtime code, and improving insights in response to user prompts.


---

## 1. Core Workflow Integration


### a. Business Rule Generation

- When a user submits a prompt (e.g., business rule question, analytics request), generate the initial business rule using your LLM or rule generator.

### b. Runtime Code Evaluation

- Pass the generated business rule, user prompt, and conversation context to the OpenEvals backend for runtime evaluation:

```python
from services.openevals_service import evaluate_business_rule

eval_result = await evaluate_business_rule(
    prompt=user_prompt,
    business_rule=generated_business_rule,
    context=conversation_context
)
```

- This returns a quality score, feedback categories, and (optionally) an improved version of the business rule.

### c. Insight Improvement

- Pass the generated insight, user prompt, and conversation context to the OpenEvals backend for improvement:

```python
from services.openevals_service import improve_insight

improved_insight = await improve_insight(
    prompt=user_prompt,
    insight=generated_insight,
    context=conversation_context
)
```

- This returns an improved version of the insight.

### d. Display Quality and Feedback

- Show the user:
  - The original business rule or insight
  - A quality score (e.g., "7.8/10" or "Good/Needs Improvement")
  - Visual indicators (colored bar, badge)
  - Option to view feedback or improvement suggestions

### e. User Feedback Collection

- Provide UI for users to:
  - Rate the business rule or insight (stars/thumbs up-down)
  - Select feedback categories (e.g., "Accuracy", "Clarity")
  - Optionally add free-text comments

### f. Continuous Learning

- All evaluations and user feedback are logged and used to further fine-tune the AI and evaluation models (handled by OpenEvals backend).

---

## 2. Frontend Integration

- Use feedback UI components:
  - Quality score badge
  - Feedback category selector
  - Improvement dialog/modal
- Example (React/TS):


```tsx
<QualityScore value={evalResult.score} />
<FeedbackCategories categories={evalResult.categories} onSubmit={handleFeedback} />
<ImprovementDialog improvedBusinessRule={evalResult.improved_business_rule} onAccept={handleAcceptImprovement} />
<ImprovedInsight improvedInsight={improved_insight} onAccept={handleAcceptImprovement} />
```

---

## 3. Backend Service Hooks

- Use `openevals_service.py` for all backend evaluation requests.

- Integrate OpenEvals calls in:
  - Business rule generation endpoints
  - Runtime code evaluation endpoints
  - Insight delivery endpoints

---

## 4. Best Practices

- **Always include full context** (prompt, prior conversation, user intent) for the most accurate evaluation.

- **Show transparency:** Let users see why a business rule or insight was scored a certain way.

- **Encourage feedback:** Make feedback UI prominent and easy to use.

- **Log all interactions** for audit and continuous improvement.

---

## 5. Example End-to-End Flow

1. User asks: “Generate a business rule to validate user input.”

2. App generates business rule and sends it to OpenEvals with the prompt/context.

3. OpenEvals returns:
    - Score: 8.5/10
    - Categories: ["Correctness", "Efficiency"]
    - Improved business rule (if any)

4. UI displays business rule, score, and “Try Improved Business Rule” button.

5. User gives feedback (“Needs more conditions”).

6. Feedback is logged and used for future improvements.

---

## 6. References

- **Backend:** `api/services/openevals_service.py`, `conversation_memory.py`
- **Frontend:** `src/components/feedback`, `src/components/analytics/QualityScore.tsx`, etc.

---

For sample code, API signatures, or UI mockups, see the referenced files or contact the maintainers.
