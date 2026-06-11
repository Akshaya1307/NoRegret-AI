from pymongo import MongoClient
from dotenv import load_dotenv
import os
import certifi

load_dotenv()

# Read MongoDB URI from .env
MONGO_URI = st.secrets["MONGO_URI"]

try:
    client = MongoClient(
        MONGO_URI,
        tlsCAFile=certifi.where()
    )

    # Test connection
    client.admin.command("ping")

    db = client["NoRegretAI"]

    opportunities_collection = db["opportunities"]
    profiles_collection = db["student_profiles"]

    print("✅ MongoDB Connected Successfully!")

except Exception as e:
    print("❌ MongoDB Connection Failed")
    print(e)

    client = None
    db = None

    opportunities_collection = None
    profiles_collection = None
