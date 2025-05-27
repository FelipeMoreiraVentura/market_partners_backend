from langchain.llms import Ollama

llm = Ollama(model="llama3") 

def gpt(messages: list, temperature: float = 0.7):
    try:
        user_prompt = ""
        for m in messages:
            if m.get("rule") == "user":
                user_prompt += m["content"]
            elif m.get("rule") == "system":
                user_prompt = m["content"] + "\n" + user_prompt

        resposta = llm(user_prompt)
        return resposta.strip()
    
    except Exception as e:
        return f"Ocorreu um erro ao gerar a resposta com o modelo local: {str(e)}"
