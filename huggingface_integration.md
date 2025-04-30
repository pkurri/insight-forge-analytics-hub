# Hugging Face Integration Guide

This guide documents the steps for making Hugging Face inference calls from your backend, as implemented in the business rules and AI services.

---

## 1. Configure Hugging Face API Settings
- Set your Hugging Face API key and model name in your `.env` or environment:
  ```env
  HUGGINGFACE_API_KEY=your_hf_api_key
  HF_MODEL_NAME=distilbert-base-uncased  # or any supported model
  ```
- These are loaded in your backend from `api/config/settings.py`.

## 2. Initialize the Hugging Face Pipeline
- In your service, initialize the Hugging Face pipeline using the configured model and token:
  ```python
  from transformers import pipeline as hf_pipeline
  from api.config.settings import get_settings

  settings = get_settings()
  hf_model_name = getattr(settings, 'HF_MODEL_NAME', 'distilbert-base-uncased')
  hf_classifier = hf_pipeline(
      'text-classification',
      model=hf_model_name,
      token=settings.HUGGINGFACE_API_KEY if hasattr(settings, 'HUGGINGFACE_API_KEY') else None
  )
  ```

## 3. Prepare the Input Data
- Format your input as required by the pipeline (for text classification, a string or list of strings):
  ```python
  input_text = "Your text to analyze"
  ```

## 4. Call the Hugging Face Pipeline
- Run inference by calling the pipeline object:
  ```python
  result = hf_classifier(input_text)
  # result: e.g. [{'label': 'LABEL_1', 'score': 0.99}]
  ```

## 5. Process the Output
- Extract relevant information from the result for your business logic (label, score, etc.).

## 6. (Optional) Handle Errors and Logging
- Wrap your call in try/except and log errors for robust production usage.

---

## Example: End-to-End Hugging Face Call
```python
from transformers import pipeline as hf_pipeline
from api.config.settings import get_settings

settings = get_settings()
hf_model_name = getattr(settings, 'HF_MODEL_NAME', 'distilbert-base-uncased')
hf_classifier = hf_pipeline(
    'text-classification',
    model=hf_model_name,
    token=settings.HUGGINGFACE_API_KEY if hasattr(settings, 'HUGGINGFACE_API_KEY') else None
)

def classify_text(text: str):
    try:
        result = hf_classifier(text)
        return result
    except Exception as e:
        print(f"Hugging Face call failed: {e}")
        return None

output = classify_text("Is this data valid?")
print(output)
```

---

## Summary Table
| Step                  | Description                                                  |
|-----------------------|--------------------------------------------------------------|
| Configure Settings    | Set API key and model in `.env`/environment                  |
| Initialize Pipeline   | Use `hf_pipeline` with model/token from settings             |
| Prepare Input         | Format input as required (string for text classification)    |
| Run Inference         | Call the pipeline object                                     |
| Process Output        | Use result in your business logic                            |
| Handle Errors         | Add error handling/logging as needed                         |

---

For other Hugging Face tasks (summarization, NER, etc.), adjust the pipeline type and input format as needed. For more advanced integration or troubleshooting, see the Hugging Face [Transformers documentation](https://huggingface.co/docs/transformers/index).
