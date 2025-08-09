# app.py
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from PIL import Image
import io

from ocr_module import extract_profile_from_image
from scraper_module import scrape_profile
from transformer_module import evaluate_with_transformer
from random_forest_module import predict_with_rf

app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
    return render_template("index.html")

import os

@app.route("/predict", methods=["POST"])
def predict():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    uploaded_file = request.files["image"]

    # Make sure uploads folder exists
    os.makedirs("uploads", exist_ok=True)

    # Save the uploaded image with its original filename
    save_path = os.path.join("uploads", uploaded_file.filename)
    uploaded_file.save(save_path)

    # Now open the saved file with PIL
    img = Image.open(save_path)

    # Proceed with OCR etc.
    ocr_data = extract_profile_from_image(img)
    if not ocr_data:
        return jsonify({"error": "OCR extraction failed"}), 500

    # ... rest of your code ...

if __name__ == "__main__":
    app.run(debug=True)
