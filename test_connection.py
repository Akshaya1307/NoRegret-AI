from mongo_utils import client

try:
    client.admin.command("ping")
    print("✅ MongoDB Connected Successfully!")

except Exception as e:
    print("❌ MongoDB Connection Failed")
    print(e)