import os
import sys
import asyncio
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def verify_environment():
    print("--- 🔍 Smarter BlinkIt Startup Verification ---")
    load_dotenv()
    
    # 1. Check .env
    required_env = ["MONGO_URI", "NEO4J_URI", "GEMINI_API_KEY", "JWT_SECRET"]
    missing = [env for env in required_env if not os.getenv(env)]
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
    else:
        print("✅ Environment variables loaded.")

    # 2. Check MongoDB
    try:
        from database import async_client
        await async_client.admin.command('ping')
        print("✅ MongoDB Atlas connection successful.")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")

    # 3. Check Neo4j
    try:
        from services.neo4j_service import get_driver
        driver = get_driver()
        if driver:
            driver.verify_connectivity()
            print("✅ Neo4j Aura connection successful.")
        else:
            print("❌ Neo4j driver not available (Package missing?)")
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")

    # 4. Check Face Recognition (Simple OpenCV)
    try:
        import cv2
        print("✅ OpenCV available.")
        from services.face_auth import encode_face_from_base64
        print("✅ Simple Face ID logic (legacy) available.")
    except ImportError as e:
        print(f"❌ Face ID dependencies missing: {e}")
    except Exception as e:
        print(f"❌ Face ID logic error: {e}")

    # 5. Check Semantic Search
    try:
        from sentence_transformers import SentenceTransformer
        print("✅ Sentence-Transformers library available.")
    except ImportError:
        print("❌ Sentence-Transformers not installed.")

    # 6. Check ZXing/PyZbar
    try:
        import zxingcpp
        print("✅ ZXing-C++ available.")
    except ImportError:
        print("❌ ZXing-C++ missing.")
    except Exception as e:
        print(f"⚠️ ZXing-C++ error (possibly missing DLL): {e}")

    try:
        from pyzbar.pyzbar import decode
        print("✅ PyZbar available.")
    except ImportError:
        print("❌ PyZbar missing.")
    except Exception as e:
        print(f"⚠️ PyZbar error (Common on Windows - missing libiconv.dll): {e}")
        print("   👉 TIP: Install Visual C++ Redistributable or ensure libiconv.dll is in your PATH.")

    print("--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(verify_environment())
