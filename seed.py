from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# Read API key from environment
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    temperature=0.5,
    messages=[
        {"role": "system", "content": "You are lab assistant, you provide accurate responses with a snarky flair."},
        {"role": "user", "content": "channel_1 = active\nchannel_2 = inactive\nchannel_3 = active\n. Which channels are active?"},
    ]
)

# print only the response content
print(completion.choices[0].message.content)