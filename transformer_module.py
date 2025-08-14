import google.generativeai as genai
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key="")  # Make sure API key is in .env

def extract_json_from_text(text):
    """Extract JSON object from string using regex."""
    try:
        json_str = re.search(r"\{.*\}", text, re.DOTALL).group()
        return json.loads(json_str)
    except Exception:
        return None

def detect_contact_details(bio):
    """Detect emails, phone numbers, and WhatsApp links in a bio."""
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    phone_pattern = r"\+?\d[\d\s\-]{7,}\d"
    whatsapp_pattern = r"(?:wa\.me|whatsapp\.com|whatsapp)"

    return {
        "emails_found": re.findall(email_pattern, bio),
        "phones_found": re.findall(phone_pattern, bio),
        "whatsapp_found": bool(re.search(whatsapp_pattern, bio, re.IGNORECASE))
    }

def is_business_bio(bio, contact_info):
    """Check if bio is business-related based on keywords or contact info."""
    business_keywords = [
        "dm for business", "order now", "shop", "store", "brand",
        "ceo", "founder", "official", "booking", "inquiries",
        "business", "buy now", "offer", "discount", "wholesale"
    ]
    bio_lower = bio.lower()

    if any(word in bio_lower for word in business_keywords):
        return True
    if contact_info["emails_found"] or contact_info["phones_found"] or contact_info["whatsapp_found"]:
        return True
    return False

def evaluate_with_transformer(profile_data):
    model = genai.GenerativeModel("gemini-1.5-flash")
    is_private = profile_data.get("is_private", False)

    # Detect contact info & business indicators
    bio_text = profile_data.get("bio", "")
    contact_info = detect_contact_details(bio_text)
    business_related = is_business_bio(bio_text, contact_info)

    # Decide profile type & strictness
    if business_related:
        profile_type = "fake business account"
        strictness_note = "Be STRICT when evaluating business accounts — scams and impersonations are common."
    else:
        profile_type = "general fake account"
        strictness_note = "Be LENIENT for personal accounts — give the benefit of doubt unless strong red flags."

    # Create tailored prompt
    if is_private:
        prompt = f"""
You are an expert investigator specialized in detecting **fake Instagram profiles**.

Given the Instagram account data below:

{{
  "username": "{profile_data.get('username')}",
  "bio": "{bio_text}",
  "is_private": true,
  "detected_contact_info": {json.dumps(contact_info)},
  "possible_profile_type": "{profile_type}"
}}

{strictness_note}

Guidelines:
- If **business account** → Be strict and score lower if there are red flags (spam claims, scam keywords, suspicious contact info).
- If **personal account** → Be lenient unless there is strong evidence of impersonation or bot behavior.
- Do NOT punish accounts just for being private.

Give a credibility score **0 (definitely fake) to 100 (definitely genuine)** and a short reasoning.

Respond ONLY with:

{{
  "ai_score": number,
  "reasoning": string
}}
"""
    else:
        prompt = f"""
You are an expert investigator specialized in detecting **fake Instagram profiles**.

Given the Instagram account data below:

{json.dumps(profile_data, indent=2)}

Detected contact info from bio: {json.dumps(contact_info)}
Possible profile type: {profile_type}

{strictness_note}

Guidelines:
- If **business account** → Be strict and score lower if there are red flags (spam claims, scam keywords, suspicious contact info).
- If **personal account** → Be lenient unless there is strong evidence of impersonation or bot behavior.
- Do NOT punish accounts just for low followers or few posts.

Give a credibility score **0 (definitely fake) to 100 (definitely genuine)** and a short reasoning.

Respond ONLY with:

{{
  "ai_score": number,
  "reasoning": string
}}
"""

    # AI Response
    response = model.generate_content(prompt)
    print("Raw AI response:", response.text)

    # Try parsing
    try:
        result = json.loads(response.text)
    except Exception:
        result = extract_json_from_text(response.text)

    if not result:
        return {"ai_score": 50, "reasoning": "Unable to evaluate"}

    # Apply bias adjustment
    score = result.get("ai_score", 50)
    if business_related:
        score = max(0, score - 15)  # More strict for business
    else:
        score = min(100, score + 10)  # More lenient for personal

    result["ai_score"] = score
    return result
