# utils/emotion_utils.py
from transformers import pipeline

# Load emotion classification model
emotion_analyzer = pipeline(
    "text-classification",
    model="cardiffnlp/twitter-roberta-base-emotion",
    return_all_scores=True
)

def detect_emotion(user_text):
    """
    Detects the dominant emotion from a given text.
    Returns (top_emotion, confidence, all_scores)
    """
    results = emotion_analyzer(user_text)
    scores = {r["label"]: r["score"] for r in results[0]}
    top_emotion = max(scores, key=scores.get)
    confidence = scores[top_emotion]
    return top_emotion, confidence, scores
