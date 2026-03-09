import asyncio
import os
import sys
from google import genai
from dotenv import load_dotenv

async def verify_user_list():
    load_dotenv('backend/.env')
    api_key = os.getenv("GEMINI_API_KEY")
    
    # EXACT names user requested
    models = [
        "gemini-3.1-flash-lite", 
        "gemini-2.5-flash-lite", 
        "gemini-2.5-flash", 
        "gemini-3-flash"
    ]
    
    client = genai.Client(api_key=api_key)
    print(f"Testing User's Requested Models:\n")
    
    for model in models:
        try:
            print(f"  [Model: {model}] ... ", end="", flush=True)
            response = client.models.generate_content(
                model=model,
                contents="OK"
            )
            print(f"✅ OK")
        except Exception as e:
            print(f"❌ {e}")

if __name__ == "__main__":
    asyncio.run(verify_user_list())
