# app.py
from flask import Flask, request, jsonify, render_template
from scraper import scrape_profile
from transformer_module import evaluate_with_transformer
from random_forest_module import predict_with_rf

app = Flask(__name__)

def safe_int(val):
    """Convert val to int safely after removing commas."""
    try:
        return int(str(val).replace(",", ""))
    except Exception:
        return 0

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        username = request.form.get("username")
        if not username:
            return render_template("index.html", error="Please enter a username")

        # Step 1: Scrape Instagram profile data (login=True if needed)
        scraped_data = scrape_profile(username, login=True)

        # Prepare a simplified profile dict for transformer (adjust keys as needed)
        profile_for_ai = {
            "username": scraped_data.get("username"),
            "bio": scraped_data.get("bio"),
            "posts": [{"caption": cap} for cap in scraped_data.get("captions", [])],
            "followers": safe_int(scraped_data.get("followers_count")),
            "posts_count": safe_int(scraped_data.get("posts_count")),
            "mutual_connections_count": scraped_data.get("mutual_count", 0),
            "is_private": scraped_data.get("is_private")
        }

        # Step 2: Get AI score + reasoning from transformer module
        ai_result = evaluate_with_transformer(profile_for_ai)
        ai_score = ai_result.get("ai_score", 50)  # default fallback

        # Step 3: Prepare dummy OCR data for RF model
        ocr_data = {
            "name": username,  # Placeholder, as you don't have OCR here
            "posts": safe_int(scraped_data.get("posts_count")),
            "followers": safe_int(scraped_data.get("followers_count")),
            "following": safe_int(scraped_data.get("following_count")),
        }

        # Step 4: Predict Fake or Genuine using Random Forest module
        rf_prediction = predict_with_rf(ai_score, scraped_data)

        # Prepare result dict
        result = {
            "username": username,
            "ai_score": ai_score,
            "ai_reasoning": ai_result.get("reasoning", ""),
            "random_forest_prediction": rf_prediction,
            "scraped_data": scraped_data,
        }

        return render_template("result.html", result=result)

    return render_template("index.html")


@app.route("/api/evaluate", methods=["POST"])
def api_evaluate():
    data = request.json
    username = data.get("username")
    if not username:
        return jsonify({"error": "username required"}), 400

    scraped_data = scrape_profile(username, login=True)

    profile_for_ai = {
        "username": scraped_data.get("username"),
        "bio": scraped_data.get("bio"),
        "posts": [{"caption": cap} for cap in scraped_data.get("captions", [])],
        "followers": safe_int(scraped_data.get("followers_count")),
        "posts_count": safe_int(scraped_data.get("posts_count")),
        "mutual_connections_count": scraped_data.get("mutual_count", 0),
        "is_private": scraped_data.get("is_private")
    }

    ai_result = evaluate_with_transformer(profile_for_ai)
    ai_score = ai_result.get("ai_score", 50)

    ocr_data = {
        "name": username,
        "posts": safe_int(scraped_data.get("posts_count")),
        "followers": safe_int(scraped_data.get("followers_count")),
        "following": safe_int(scraped_data.get("following_count")),
    }

    rf_prediction = predict_with_rf(ai_score, ocr_data, scraped_data)

    return jsonify({
        "username": username,
        "ai_score": ai_score,
        "ai_reasoning": ai_result.get("reasoning", ""),
        "random_forest_prediction": rf_prediction,
        "scraped_data": scraped_data,
    })


if __name__ == "__main__":
    app.run(debug=True)
