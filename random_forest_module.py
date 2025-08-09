# random_forest_module.py
import joblib
import pandas as pd
import numpy as np
from model import extract_features  # put your extract_features in here

model = joblib.load("rf_model.pkl")

def predict_with_rf(ai_score, ocr_data, scraped_data):
    # Step 1: Build raw DataFrame with the same column names your feature extractor expects
    raw_data = {
        "name": ocr_data.get("name", ""),
        "statuses_count": ocr_data.get("posts", 0),
        "followers_count": ocr_data.get("followers", 0),
        "friends_count": ocr_data.get("following", 0),
        "favourites_count": scraped_data.get("favourites_count", 0),  # or 0 if not available
        "description": scraped_data.get("bio", "")
    }

    df = pd.DataFrame([raw_data])

    # Step 2: Extract model-ready features
    X = extract_features(df)

    # Step 3: Add AI score if model was trained with it
    if "ai_score" in model.feature_names_in_:
        X["ai_score"] = ai_score

    # Step 4: Predict
    pred = model.predict(X)[0]
    return "Fake" if pred == 1 else "Genuine"
