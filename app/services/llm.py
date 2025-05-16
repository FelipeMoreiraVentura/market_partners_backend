import re
import aiohttp
import os
import json

async def invoke_chute(menssages: list, temperature: float):
    api_token = os.getenv("DEEPSEEKAPI")

    headers = {
        "Authorization": "Bearer " + api_token,
        "Content-Type": "application/json"
    }
    
    body = {
        "model": "deepseek-ai/DeepSeek-V3-0324",
        "messages":menssages,
        "stream": False,
        "max_tokens": 1024,
        "temperature": temperature
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://llm.chutes.ai/v1/chat/completions", 
            headers=headers,
            json=body
        ) as response:
            data = await response.json()
            if 'choices' in data and len(data['choices']) > 0:
                return data['choices'][0]['message']['content']
            else:
                return f"Resposta inesperada da API: {json.dumps(data, indent=2)}"
