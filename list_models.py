import os
from google import genai
from dotenv import load_dotenv

def list_models():
    load_dotenv('backend/.env')
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("No API key found.")
        return

    client = genai.Client(api_key=api_key)
    print(f"--- Available Models for key {api_key[:8]}... ---")
    try:
        for model in client.models.list():
            print(f"Name: {model.name}, Supported: {model.supported_actions}")
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    list_models()
