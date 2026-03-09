import asyncio
import os
import sys
from dotenv import load_dotenv

# Add current directory to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from backend.services.ai.gemini_service import gemini_service

async def test_gemini():
    load_dotenv('backend/.env')
    print("--- Testing Gemini Service ---")
    prompt = "Tell me a joke about groceries."
    result = await gemini_service.generate_content(prompt)
    if result:
        print("✅ SUCCESS!")
        print("Response:", result[:100], "...")
    else:
        print("❌ FAILED: Still temporarily unavailable.")

if __name__ == "__main__":
    asyncio.run(test_gemini())
