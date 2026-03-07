import os
import asyncio
from dotenv import load_dotenv
from google import genai

load_dotenv()

async def test_genai_v2():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY not found in .env")
        return

    print(f"Key found: {api_key[:10]}...")
    
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents="Say hello"
        )
        print(f"✅ SUCCESS: {response.text}")
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_genai_v2())
