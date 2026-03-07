import os
import sys
import asyncio
import json

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google import genai
from dotenv import load_dotenv

load_dotenv()

async def verify_keys():
    print("--- Gemini API Key Verification ---")
    
    # Support multiple keys
    # User added them to GEMINI_API_KEY as a comma-separated string
    keys_env = os.getenv("GEMINI_API_KEYS", "") or os.getenv("GEMINI_API_KEY", "")
    api_keys = [k.strip() for k in keys_env.split(",") if k.strip()]
    
    print(f"Found {len(api_keys)} keys to test.")

    for i, key in enumerate(api_keys):
        print(f"\n[KEY_{i+1}] Testing: {key[:8]}...")
        client = genai.Client(api_key=key)
        try:
            # We try gemini-2.0-flash
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents="Identify yourself."
            )
            print(f"✅ [KEY_{i+1}] SUCCESS: {response.text.strip()[:30]}...")
        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower():
                print(f"⚠️ [KEY_{i+1}] QUOTA EXCEEDED (429)")
            else:
                print(f"❌ [KEY_{i+1}] FAILED: {err[:100]}...")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(verify_keys())
