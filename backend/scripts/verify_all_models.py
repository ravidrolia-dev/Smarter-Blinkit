import os
import sys
import asyncio
from google import genai
from dotenv import load_dotenv

load_dotenv()

MODEL_PRIORITY = [
    "gemini-3.1-flash-lite-preview",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-3-flash-preview",
]

async def verify_keys():
    print("🚀 --- System-Wide API Key & Model Verification ---")
    
    # Support multiple keys
    keys_env = os.getenv("GEMINI_API_KEYS", "") or os.getenv("GEMINI_API_KEY", "")
    api_keys = [k.strip() for k in keys_env.split(",") if k.strip()]
    
    if not api_keys:
        print("❌ ERROR: No API keys found in .env (GEMINI_API_KEY)")
        return

    print(f"📡 Found {len(api_keys)} keys to test.")

    for i, key in enumerate(api_keys):
        print(f"\n🔑 [KEY_{i+1}] Testing ({key[:8]}...)")
        client = genai.Client(api_key=key)
        
        for model in MODEL_PRIORITY:
            print(f"  - Model: {model}", end=" ", flush=True)
            try:
                # Simple probe request
                response = client.models.generate_content(
                    model=model,
                    contents="Hi"
                )
                print(f"✅ WORKS")
            except Exception as e:
                err = str(e).lower()
                if "429" in err or "quota" in err or "resource_exhausted" in err:
                    print(f"⚠️ QUOTA EXCEEDED (429)")
                elif "404" in err or "not found" in err:
                    print(f"❌ MODEL NOT FOUND")
                elif "403" in err or "permission" in err:
                    print(f"❌ PERMISSION DENIED (Invalid Key?)")
                else:
                    print(f"❌ ERROR: {str(e)[:50]}")

    print("\n✅ Verification Complete.")

if __name__ == "__main__":
    asyncio.run(verify_keys())
