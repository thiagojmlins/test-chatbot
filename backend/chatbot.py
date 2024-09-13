import os
import openai
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def generate_reply(message_content: str) -> str:
    try:
        # Call the OpenAI API with the message content
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": message_content}
            ]
        )

        # Extract the chatbot's response from the API
        return response.choices[0].message.content

    except openai.OpenAIError as e:
        # Handle any API errors (e.g., network issues, rate limits)
        return f"Error communicating with OpenAI: {str(e)}"
