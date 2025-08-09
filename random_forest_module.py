import joblib
import pandas as pd
import numpy as np
from model import extract_features  # Make sure this matches your model file

# Load pretrained RF model
model = joblib.load("rf_model.pkl")

def safe_int(val):
    """Convert strings like '3,923' to int 3923, or 0 if invalid."""
    if not val:
        return 0
    try:
        return int(str(val).replace(",", ""))
    except Exception:
        return 0

def predict_with_rf(ai_score, scraped_data):
    """
    Predict fake or genuine profile using AI score + scraped data.

    ai_score    : float, AI credibility score (0-100)
    scraped_data: dict, profile data scraped from Instagram
    """
    name= scraped_data.get("name", "")
    posts_count = safe_int(scraped_data.get("posts_count"))
    followers_count = safe_int(scraped_data.get("followers_count"))
    following_count = safe_int(scraped_data.get("following_count"))
    favourites_count = safe_int(scraped_data.get("favourites_count"))

    bio_text = scraped_data.get("bio", "") or ""
    description_len = len(bio_text)

    # Match exactly the model features!
    raw_data = {
        "name":name,
        "statuses_count": posts_count,
        "followers_count": followers_count,
        "friends_count": following_count,
        "favourites_count": favourites_count,
        "desc_length": description_len
    }

    df = pd.DataFrame([raw_data])

    X = extract_features(df)

    # Add AI score if model expects it
    if hasattr(model, "feature_names_in_") and "ai_score" in model.feature_names_in_:
        X["ai_score"] = ai_score

    X = X.replace([np.inf, -np.inf], np.nan).fillna(0)

    pred = model.predict(X)[0]
    return "Fake" if pred == 1 else "Genuine"

# Quick test
if __name__ == "__main__":
    dummy_ai_score = 75.0
    dummy_scraped_data = {
        "name": "jonnysinn",
        "posts_count": "0",
        "followers_count": "0",
        "following_count": "0",
        "favourites_count": "0",
        "bio": "the world is in my control hbcqicyuwbcyu hci3be"
    }

    print(predict_with_rf(dummy_ai_score, dummy_scraped_data))
