# ocr_module.py
import google.generativeai as genai
import json
from dotenv import load_dotenv
from PIL import Image

# Load .env file
load_dotenv()

# Get API key from environment
API_KEY = "AIzaSyBkT_u1rTrpFk5DyFiTCOqv3o3kBgKbSZk";
# Clear error if API key is missing
if not API_KEY:
    raise ValueError(
        "❌ GOOGLE_API_KEY not found. Please set it in a .env file like:\n"
        "GOOGLE_API_KEY=your_real_key_here\n"
        "Also ensure the .env file is in the same directory where you run the script."
    )

# Configure Gemini
genai.configure(api_key=API_KEY)

def extract_profile_from_image(image):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = """
    Extract the following details in JSON format from this social media profile screenshot:
    {
      "username": "...",
      "followers": 0,
      "following": 0,
      "posts": 0,
      "description": "..."
    }
    """
    response = model.generate_content([prompt])  # Send prompt
    print("OCR raw response:", response.text)

    try:
        # Parse response text as JSON (assuming response.text contains JSON string)
        data = json.loads(response.text)
        return data
    except json.JSONDecodeError as e:
        print("Failed to parse JSON from OCR response:", e)
        return None
