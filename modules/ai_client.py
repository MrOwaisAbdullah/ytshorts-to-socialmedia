from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

# Set up Gemini API client
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set")
client = genai.Client(api_key=api_key)
model_name = "gemini-2.0-flash"