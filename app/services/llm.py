from openai import OpenAI
import os

client = OpenAI(api_key="")

def gpt(messages: list, temperature: float = 0.7):
    try:
        openai_messages = []
        for m in messages:
            role = m.get("role", "user")
            openai_messages.append({"role": role, "content": m["content"]})

        response = client.chat.completions.create(
            model="gpt-3.5-turbo", 
            messages=openai_messages,
            temperature=temperature,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Ocorreu um erro ao gerar a resposta com o modelo OpenAI: {str(e)}"
