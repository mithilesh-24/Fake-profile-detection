import google.generativeai as genai
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key="AIzaSyBkT_u1rTrpFk5DyFiTCOqv3o3kBgKbSZk")  # Use your .env API key securely

def extract_json_from_text(text):
    """
    Attempt to extract JSON object from a string using regex.
    """
    try:
        json_str = re.search(r"\{.*\}", text, re.DOTALL).group()
        return json.loads(json_str)
    except Exception:
        return None

def evaluate_with_transformer(profile_data):
    model = genai.GenerativeModel("gemini-1.5-flash")
    is_private = profile_data.get("is_private", False)

    if is_private:
        prompt = f"""
You are an expert assistant specialized in detecting fake Instagram profiles.

Given the Instagram account data below:

{{
  "username": "{profile_data.get('username')}",
  "bio": "{profile_data.get('bio', '')}",
  "is_private": true
}}

Since this account is private and no posts or captions are accessible, evaluate the likelihood that this account is fake by carefully considering:

- The content and tone of the bio.
- Presence of suspicious phrases, spam-like language, or unnatural wording.
- Any hints of impersonation or inconsistencies in the bio.
- The fact that profile privacy alone is not a reliable indicator of fakery.
- Avoid making assumptions based solely on lack of visible posts or followers.

Provide a nuanced evaluation and a detailed explanation supporting your credibility score.

Respond ONLY with a JSON object containing exactly these keys:

{{
  "ai_score": number,  // 0 (definitely fake) to 100 (definitely genuine)
  "reasoning": string  // detailed explanation of your evaluation
}}

Do NOT include any text outside this JSON or extra formatting.
"""
    else:
        prompt = f"""
You are an expert assistant specialized in detecting fake Instagram profiles.

Given the Instagram account data below, including username, bio, posts, followers, and other metadata:

{json.dumps(profile_data, indent=2)}

Evaluate how genuine or fake this account is by carefully considering:

- The quality, authenticity, and coherence of the bio.
- Consistency and realism of posts and captions (e.g., avoid spam, repetitive, or suspicious content).
- Number of followers and mutual connections relative to activity.
- Signs of automated or bot behavior.
- Any inconsistencies, red flags, or indicators of impersonation.
- Whether the account appears to promote scams, misinformation, or suspicious links.
- Avoid false positives by carefully balancing red flags with realistic exceptions.

Assign a credibility score between 0 (fake) and 100 (genuine).

Provide a detailed reasoning supporting your score.

Respond ONLY with a JSON object containing exactly these keys:

{{
  "ai_score": number,
  "reasoning": string
}}

Do NOT include any additional text or formatting.
"""

    response = model.generate_content(prompt)
    print("Raw AI response:", response.text)

    try:
        return json.loads(response.text)
    except Exception as e:
        extracted = extract_json_from_text(response.text)
        if extracted is not None:
            return extracted
        print(f"JSON parsing error: {e}")
        return {"ai_score": 50, "reasoning": "Unable to evaluate"}