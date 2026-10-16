import time
from dotenv import load_dotenv
from google import genai
from google.genai import types, errors
from pydantic import BaseModel

load_dotenv()
client = genai.Client()

class Task(BaseModel):
    title: str
    priority: int          # 1 = high, 3 = low
    tags: list[str]

text = "Kal tak GitHub par GFG solutions upload karne hain, important hai."

for attempt in range(4):
    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=f"Is text se task nikalo: {text}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=Task,
            ),
        )
        task = Task.model_validate_json(response.text)
        print(task)
        print(task.title, task.priority, task.tags)
        break
    except errors.ServerError as e:
        wait = 2 ** attempt * 3
        print(f"Server busy ({e.code}), {wait}s baad dobara try...")
        time.sleep(wait)