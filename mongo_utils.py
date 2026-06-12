from pymongo import MongoClient
import certifi
import streamlit as st

# Initialize defaults
client = None
db = None
opportunities_collection = None
profiles_collection = None

try:
    # Read from Streamlit Secrets
    MONGO_URI = st.secrets["MONGO_URI"]

    # Connect to MongoDB Atlas
    client = MongoClient(
        MONGO_URI,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=10000
    )

    # Test connection
    client.admin.command("ping")

    # Database
    db = client["NoRegretAI"]

    # Collections
    opportunities_collection = db["opportunities"]
    profiles_collection = db["student_profiles"]

    st.sidebar.success("✅ MongoDB Connected")

except Exception as e:
    st.sidebar.error(f"❌ MongoDB Error: {e}")

    client = None
    db = None
    opportunities_collection = None
    profiles_collection = None
