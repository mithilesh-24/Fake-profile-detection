import google.generativeai as genai
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key="AIzaSyBkT_u1rTrpFk5DyFiTCOqv3o3kBgKbSZk")

def extract_json_from_text(text):
    """
    Try to extract JSON object from a string.
    """
    try:
        json_str = re.search(r"\{.*\}", text, re.DOTALL).group()
        return json.loads(json_str)
    except Exception:
        return None

def evaluate_with_transformer(profile_data):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
You are an assistant. Given the account data below:

{json.dumps(profile_data, indent=2)}

Evaluate the credibility of this account as a number from 0 (fake) to 100 (genuine).

Respond ONLY with a JSON object, with exactly these keys:

{{
  "ai_score": number,
  "reasoning": string
}}

Do NOT include any other text, explanation, or formatting.
"""
    response = model.generate_content(prompt)
    print("Raw AI response:", response.text)  # Debug print

    # Try parsing response as JSON directly
    try:
        return json.loads(response.text)
    except Exception as e:
        # If direct parsing fails, try to extract JSON substring
        extracted = extract_json_from_text(response.text)
        if extracted is not None:
            return extracted

        print("JSON parsing error:", e)
        return {"ai_score": 50, "reasoning": "Unable to evaluate"}
