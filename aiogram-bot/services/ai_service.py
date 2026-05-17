from openai import AsyncOpenAI
import os


def get_client():
    return AsyncOpenAI(
        api_key=os.getenv("API_KEY"),
        base_url=os.getenv("BOTHUB_BASE_URL")
    )

MODEL = os.getenv("JOKE_MODEL", "gpt-3.5-turbo")

async def get_ai_response(name: str, activity: str, user_message: str):
    client = get_client()
    
    prompt = f"Ты эксперт по хобби. Пользователь {name} очень любит {activity}. Обсуди с ним это увлечение, дай рекомендации. Будь дружелюбен и вежлив."
    
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_message}
        ]
    )

    await client.close()
    
    return response.choices[0].message.content
