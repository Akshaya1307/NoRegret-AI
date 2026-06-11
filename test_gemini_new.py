from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

print("Testing Gemini API connection...")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Say hello in 3 words"
)

print(response.text)