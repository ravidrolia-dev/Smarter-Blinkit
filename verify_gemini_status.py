import asyncio
import os
import sys
from google import genai
from dotenv import load_dotenv

async def verify_all():
    load_dotenv('backend/.env')
    keys_env = os.getenv("GEMINI_API_KEYS", "") or os.getenv("GEMINI_API_KEY", "")
    api_keys = [k.strip() for k in keys_env.split(",") if k.strip()]
    
    # Models we configured
    models = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-3.1-flash-lite-preview"]
    
    print(f"Testing {len(api_keys)} keys across {len(models)} models...\n")
    
    for i, key in enumerate(api_keys):
        print(f"--- Testing KEY_{i+1} ({key[:8]}...) ---")
        client = genai.Client(api_key=key)
        for model in models:
            try:
                # Use synchronous call for simplicity in test script if possible, or stay async
                print(f"  [Model: {model}] ... ", end="", flush=True)
                response = client.models.generate_content(
                    model=model,
                    contents="Hi. Reply with 'OK'."
                )
                if response and response.text:
                    print(f"✅ WORKS")
                else:
                    print(f"❓ EMPTY RESPONSE")
            except Exception as e:
                err = str(e).lower()
                if "429" in err or "quota" in err or "resource_exhausted" in err:
                    print(f"❌ QUOTA EXHAUSTED")
                elif "404" in err:
                    print(f"❌ NOT FOUND")
                else:
                    print(f"❌ ERROR: {e}")
        print()

if __name__ == "__main__":
    asyncio.run(verify_all())
