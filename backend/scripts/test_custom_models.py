import os
import asyncio
from google.genai import Client
from dotenv import load_dotenv

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

async def check_custom_models():
    keys_env = os.getenv("GEMINI_API_KEYS", "") or os.getenv("GEMINI_API_KEY", "")
    keys = [k.strip() for k in keys_env.split(",") if k.strip()]
    
    models = [
        "gemini-3.1-flash-lite-preview",
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
        "gemini-3-flash-preview"
    ]
    
    print("=" * 60)
    print("   CUSTOM MODEL CONNECTIVITY TEST")
    print("=" * 60)
    
    for i, key in enumerate(keys):
        print(f"\n[KEY {i+1}] {key[:10]}...")
        client = Client(api_key=key)
        for model in models:
            print(f"  - Testing {model:30} ...", end=" ")
            try:
                response = await client.aio.models.generate_content(
                    model=model, 
                    contents="Hi"
                )
                if response.text:
                    print("✅ Working")
                else:
                    print("❓ Empty Response")
            except Exception as e:
                msg = str(e).lower()
                if "429" in msg or "quota" in msg:
                    print("❌ Quota Exceeded")
                elif "404" in msg:
                    print("❌ Not Found")
                else:
                    print(f"❌ Error: {msg[:50]}...")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(check_custom_models())
