import time
from flask import Flask, request, jsonify, render_template
from scraper import scrape_profile
from transformer_module import evaluate_with_transformer
from random_forest_module import predict_with_rf
import mysql.connector
import json

app = Flask(__name__)

def safe_int(val):
    """Convert val to int safely after removing commas."""
    try:
        return int(str(val).replace(",", ""))
    except Exception:
        return 0

def save_result_to_db(result):
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # default XAMPP password is empty, update if you set one
            database="insta_evaluation"
        )
        cursor = conn.cursor()

        insert_query = """
        INSERT INTO profile_evaluations
        (username, ai_score, ai_reasoning, random_forest_prediction, scraped_data)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            result["username"],
            result["ai_score"],
            result["ai_reasoning"],
            result["random_forest_prediction"],
            json.dumps(result["scraped_data"])
        ))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error saving to DB: {e}")

def get_result_from_db(username):
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # your MySQL password if any
            database="insta_evaluation"
        )
        cursor = conn.cursor(dictionary=True)  # fetch results as dict

        query = """
        SELECT * FROM profile_evaluations 
        WHERE username = %s 
        ORDER BY evaluated_at DESC 
        LIMIT 1
        """
        cursor.execute(query, (username,))
        row = cursor.fetchone()

        cursor.close()
        conn.close()

        if row:
            # Convert JSON string back to dict
            row["scraped_data"] = json.loads(row["scraped_data"])
            return row
        else:
            return None
    except Exception as e:
        print(f"Error fetching from DB: {e}")
        return None

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        start_time = time.time()
    if request.method == "POST":
        username = request.form.get("username")
        if not username:
            return render_template("index.html", error="Please enter a username")

        # Map RF string label to numeric value
        rf_map = {"Fake": 0, "Genuine": 1, "Mostly Fake": 0, "Mostly Genuine": 1}

        # 1) Check if username exists in DB
        saved_result = get_result_from_db(username)
        if saved_result:
            ai_score = float(saved_result["ai_score"])
            rf_prediction_str = saved_result["random_forest_prediction"]
            rf_pred = rf_map.get(rf_prediction_str, 0)

            combined_score = 0.7 * ((ai_score) /100) + 0.3 * rf_pred
            final_label = "Mostly Genuine" if combined_score >= 0.5 else "Mostly Fake"
            print(f"Using cached result for {username}: AI Score: {ai_score}, RF Prediction: {rf_prediction_str}")
            result = {
                "username": saved_result["username"],
                "final_label": final_label,
            }
            elapsed = time.time() - start_time
            if elapsed < 5:
                time.sleep(5 - elapsed)
            return render_template("index.html", result=result, scroll_to="result")

        # 2) Not found, scrape and evaluate
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
        ai_score = float(ai_result.get("ai_score", 50))  # ensure float

        rf_prediction = predict_with_rf(ai_score, scraped_data)  # returns string label
        rf_pred = rf_map.get(rf_prediction, 0)  # map to 0 or 1 safely

        combined_score = 0.7 * ((ai_score) /100) + 0.3 * rf_pred
        final_label = "Mostly Genuine" if combined_score >= 0.5 else "Mostly Fake"

        result = {
            "username": username,
            "final_label": final_label,
        }

        # Save raw data and predictions for reference
        save_result_to_db({
            "username": username,
            "ai_score": ai_score,
            "ai_reasoning": ai_result.get("reasoning", ""),
            "random_forest_prediction": rf_prediction,
            "scraped_data": scraped_data,
        })

        return render_template("index.html", result=result, scroll_to="result")

    return render_template("index.html",result=None, scroll_to=None)


@app.route("/api/evaluate", methods=["POST"])
def api_evaluate():
    data = request.json
    username = data.get("username")
    if not username:
        return jsonify({"error": "username required"}), 400

    rf_map = {"Fake": 0, "Genuine": 1, "Mostly Fake": 0, "Mostly Genuine": 1}

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
    ai_score = float(ai_result.get("ai_score", 50))
    rf_prediction = predict_with_rf(ai_score, scraped_data)
    rf_pred = rf_map.get(rf_prediction, 0)
    print(f"AI Score: {ai_score}, RF Prediction: {rf_prediction}")
    combined_score =  1*(ai_score / 100) + 0.3 * rf_pred
    final_label = "Mostly Genuine" if combined_score >= 0.5 else "Mostly Fake"

    return jsonify({
        "username": username,
        "final_label": final_label,
    })


if __name__ == "__main__":
    app.run(debug=True)
