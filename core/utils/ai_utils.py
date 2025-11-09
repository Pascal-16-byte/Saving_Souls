
"""
core/ai_utils.py

Uses huggingface_hub.InferenceClient for sentiment analysis (with graceful fallbacks)
and for chat completions. Falls back to a local heuristic if remote inference fails.
"""
import os
import random
import logging
from typing import Dict, Any, Optional

from huggingface_hub import InferenceClient

# --- Logging setup ---
logger = logging.getLogger("core.ai_utils")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s core.ai_utils: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# --- API Configuration ---
HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
client = InferenceClient(token=HF_API_KEY) if HF_API_KEY else InferenceClient()

# --- Candidate sentiment models (order matters) ---
CANDIDATE_SENTIMENT_MODELS = [
    "cardiffnlp/twitter-roberta-base-sentiment",
    "finiteautomata/bertweet-base-sentiment-analysis",
    "distilbert/distilbert-base-uncased-finetuned-sst-2-english",
]

# --- Fallback responses ---
FALLBACK_RESPONSES = [
    "I’m here for you. You’re not alone in this, and it’s okay to reach out for help. 💙",
    "That sounds really tough. Remember to take things one step at a time — you’re doing your best. 🌼",
    "Your feelings matter. Let’s talk about what’s been troubling you. 🤍",
    "It’s okay to feel this way sometimes. You deserve care and kindness, especially from yourself. 💫",
]

def _normalize_label(label: str) -> str:
    if not label:
        return ""
    return label.strip().lower()

def analyze_sentiment(text: str) -> Dict[str, Any]:
    """
    Use InferenceClient.text_classification on a list of candidate models.
    Returns a dict with:
      - distress_flag: "true" or "false"
      - distress_level: "high" / "medium" / "low" / "unknown"
      - model_used: which model produced the result (or 'local_fallback')
      - raw: optional raw model output for debugging
    Gracefully handles HF errors (including 410 Gone) and falls back to a local heuristic.
    """
    logger.info("Analyzing sentiment for text (len=%d)...", len(text))

    for model in CANDIDATE_SENTIMENT_MODELS:
        try:
            logger.info("Trying sentiment model: %s", model)
            # The InferenceClient provides high-level helpers for tasks.
            # text_classification returns a list of TextClassificationOutputElement
            result = client.text_classification(text, model=model)
            # result is typically a list-like of TextClassificationOutputElement
            # Convert to native python structures if needed
            if not result:
                logger.warning("Model %s returned empty result; trying next model.", model)
                continue

            # Some models return a list of labels, others return single dict/list.
            # We'll inspect the first element.
            first = result[0]
            # Elements typically have .label and .score attributes OR are dict-like
            label = getattr(first, "label", None) or (first.get("label") if isinstance(first, dict) else None)
            score = getattr(first, "score", None) or (first.get("score") if isinstance(first, dict) else None)

            label_norm = _normalize_label(label)
            score = float(score) if score is not None else 0.0

            logger.info("Model %s returned label=%s score=%.3f", model, label_norm, score)

            # Decide distress based on label and score heuristics
            if "neg" in label_norm or "negative" in label_norm or label_norm.startswith("label_0") or label_norm.startswith("0"):
                if score > 0.75:
                    return {"distress_flag": "true", "distress_level": "high", "model_used": model, "raw": result}
                elif score > 0.5:
                    return {"distress_flag": "true", "distress_level": "medium", "model_used": model, "raw": result}
                else:
                    return {"distress_flag": "true", "distress_level": "low", "model_used": model, "raw": result}
            else:
                # positive / neutral
                return {"distress_flag": "false", "distress_level": "low", "model_used": model, "raw": result}

        except Exception as e:
            # Inspect exception text for common HF HTTP errors (e.g., 410 Gone)
            msg = str(e)
            logger.warning("Sentiment model %s failed: %s", model, msg)
            # continue to next model on any failure
            continue

    # If we reach here, all remote attempts failed -> local heuristic fallback
    logger.warning("All HF sentiment attempts failed — using local fallback heuristic.")
    lowered = text.lower()

    # high-severity keywords
    high_keywords = [
        "suicide", "kill myself", "i want to die", "can't go on", "worthless",
        "end my life", "i'm going to kill myself", "i will kill myself", "die by suicide"
    ]
    if any(k in lowered for k in high_keywords):
        return {"distress_flag": "true", "distress_level": "high", "model_used": "local_fallback", "raw": None}

    weak_negatives = ["sad", "down", "upset", "stressed", "anxious", "overwhelmed", "depressed", "lonely", "hopeless"]
    neg_count = sum(1 for k in weak_negatives if k in lowered)
    if neg_count >= 2:
        return {"distress_flag": "true", "distress_level": "medium", "model_used": "local_fallback", "raw": None}

    return {"distress_flag": "false", "distress_level": "low", "model_used": "local_fallback", "raw": None}


# ---------------------------
# Chat (supportive reply) utilities using InferenceClient.chat (keeps previous behavior)
# ---------------------------
CHAT_MODEL = "NousResearch/Hermes-2-Pro-Llama-3-8B"

def generate_supportive_reply(user_text: str) -> str:
    """
    Generate a supportive reply using the chat completion endpoint via InferenceClient.
    Falls back to a local randomized supportive message on error.
    """
    try:
        logger.info("Generating supportive reply using model: %s", CHAT_MODEL)
        completion = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{"role": "user", "content": user_text}],
            max_tokens=150,
            temperature=0.8,
            top_p=0.9,
        )
        # completion.choices[0].message["content"] is the expected structure
        reply = None
        if hasattr(completion, "choices") and len(completion.choices) > 0:
            # Some client versions return objects, others dict-like
            first = completion.choices[0]
            # attempt several access patterns
            reply = getattr(first, "message", None)
            if reply and isinstance(reply, dict):
                reply = reply.get("content")
            elif reply and hasattr(reply, "get"):
                reply = reply.get("content") if isinstance(reply, dict) else None
            elif isinstance(first, dict):
                # dict-like structure
                r = first.get("message") or first.get("text") or first.get("content")
                if isinstance(r, dict):
                    reply = r.get("content") or r.get("text")
                else:
                    reply = r
        # final fallback if reply still None
        if not reply:
            logger.warning("HF chat completion returned no content; using local fallback.")
            return random.choice(FALLBACK_RESPONSES)
        return reply.strip()
    except Exception as e:
        logger.error("HF Chat Model Error: %s", e)
        return random.choice(FALLBACK_RESPONSES)
