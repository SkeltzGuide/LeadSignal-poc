import os
import google.generativeai as genai
from google.adk.agents import Agent

import random

# -- Setup --
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "0"  # Use public Gemini endpoint
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

async def generate_key() -> int:
    """Tool that generates a random key"""
    key = random.randint(0,1000)
    return key

# PA agent
key_agent = Agent(
    name="key_agent",
    instruction="You use your tools to generate a random key value - only provide the key itself, no text",
    model="gemini-2.5-flash",
    tools=[
        generate_key
        ]
) # switched to google agent framework

