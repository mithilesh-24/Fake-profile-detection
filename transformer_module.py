import google.generativeai as genai
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key="AIzaSyBkT_u1rTrpFk5DyFiTCOqv3o3kBgKbSZk")  

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

    # Select prompt type
    if business_related:
        profile_type = "fake business account"
    else:
        profile_type = "general fake account"

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

Evaluate the likelihood that this account is a **{profile_type}** by considering the available data.
Provide a credibility score **0 (definitely fake) to 100 (definitely genuine)** and a detailed explanation.

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

Evaluate the likelihood that this account is a **{profile_type}** by considering:

- Bio content and realism
- Consistency between posts, captions, followers
- Engagement quality
- Signs of spam, impersonation, or scams

Provide a credibility score **0 (definitely fake) to 100 (definitely genuine)** and a detailed explanation.

Respond ONLY with:

{{
  "ai_score": number,
  "reasoning": string
}}
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
