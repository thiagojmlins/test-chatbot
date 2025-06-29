import openai
from openai import OpenAI
from core.config import API_KEY, API_MODEL

client = OpenAI(api_key=API_KEY)

def generate_reply(message_content: str) -> str:
    try:
        # Call the OpenAI API with the message content
        response = client.chat.completions.create(
            model=API_MODEL,
            messages=[
                {"role": "user", "content": message_content}
            ]
        )

        # Extract the chatbot's response from the API
        return response.choices[0].message.content

    except openai.OpenAIError as e:
        # Handle any API errors (e.g., network issues, rate limits)
        return f"Error communicating with LLM: {str(e)}"
