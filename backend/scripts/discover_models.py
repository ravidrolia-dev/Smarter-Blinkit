import os
import sys
from google import genai
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def list_gemini_models():
    print("\n--- Listing Available Gemini Models ---")
    keys_env = os.getenv("GEMINI_API_KEYS", "") or os.getenv("GEMINI_API_KEY", "")
    api_key = [k.strip() for k in keys_env.split(",") if k.strip()][0]
    
    client = genai.Client(api_key=api_key)
    try:
        for m in client.models.list():
            print(f"- {m.name}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_gemini_models()
