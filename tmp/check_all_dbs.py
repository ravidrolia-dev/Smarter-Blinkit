from pymongo import MongoClient
import os

def check():
    # Check Localhost
    print("Checking Localhost...")
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        print("Local Dbs:", client.list_database_names())
        if "smarter_blinkit" in client.list_database_names():
            print("Local Smarter-Blinkit Product Count:", client.smarter_blinkit.products.count_documents({}))
        client.close()
    except Exception as e:
        print("Localhost not reachable:", e)
    
    # Check Atlas (if ENV loaded)
    from dotenv import load_dotenv
    load_dotenv("a:/console/Smarter-Blinkit/backend/.env")
    uri = os.getenv("MONGO_URI")
    if uri:
        print("\nChecking Atlas...")
        client = MongoClient(uri)
        print("Atlas Smarter-Blinkit Product Count:", client.smarter_blinkit.products.count_documents({}))
        client.close()

if __name__ == "__main__":
    check()
