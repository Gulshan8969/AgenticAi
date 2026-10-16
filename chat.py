import time
from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()
client = genai.Client()

for attempt in range(4):
    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents="Agentic AI kya hota hai? 2 line me batao.",
        )
        print(response.text)
        break
    except errors.ServerError as e:
        wait = 2 ** attempt * 3
        print(f"Server busy ({e.code}), {wait}s baad dobara try...")
        time.sleep(wait)
else:
    print("Kai baar try karne par bhi nahi chala, thodi der baad try karein.")