import asyncio
import os
import sys
from google import genai
from dotenv import load_dotenv

async def final_status_report():
    load_dotenv('backend/.env')
    
    # 1. Get Keys
    keys_env = os.getenv("GEMINI_API_KEYS", "") or os.getenv("GEMINI_API_KEY", "")
    api_keys = [k.strip() for k in keys_env.split(",") if k.strip()]
    
    # 2. Priority Models
    models = [
        "gemini-3.1-flash-lite-preview", 
        "gemini-2.5-flash-lite", 
        "gemini-2.5-flash", 
        "gemini-3-flash-preview"
    ]
    
    print(f"--- Final Gemini Verification ---")
    print(f"Keys Found: {len(api_keys)}")
    
    for i, key in enumerate(api_keys):
        print(f"\n🔑 KEY_{i+1} ({key[:8]}...):")
        client = genai.Client(api_key=key)
        for model in models:
            try:
                print(f"  - [{model}] ... ", end="", flush=True)
                response = client.models.generate_content(
                    model=model,
                    contents="Hi."
                )
                if response:
                    print(f"✅ WORKS")
                else:
                    print(f"❓ NO RESPONSE")
            except Exception as e:
                print(f"❌ {str(e)[:50]}...")

if __name__ == "__main__":
    asyncio.run(final_status_report())
