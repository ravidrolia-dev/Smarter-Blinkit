import os
import sys
from google import genai
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def test_3_1():
    print("\n--- Direct Test: gemini-3.1-flash-lite-preview ---")
    keys_env = os.getenv("GEMINI_API_KEYS", "") or os.getenv("GEMINI_API_KEY", "")
    api_key = [k.strip() for k in keys_env.split(",") if k.strip()][0]
    
    client = genai.Client(api_key=api_key)
    try:
        # Try both with and without preview if needed, but list() showed preview
        model_id = "gemini-3.1-flash-lite-preview"
        print(f"Testing {model_id}...")
        response = client.models.generate_content(
            model=model_id,
            contents="Say '3.1 is alive'"
        )
        print(f"✅ Success: {response.text.strip()}")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    test_3_1()
