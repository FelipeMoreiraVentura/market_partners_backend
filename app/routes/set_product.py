import json
from app.schemas.set_product import setProductProps
from app.services.llm import gpt

def setProductRoute(payload: setProductProps):
    prompt = f"""
Você é um gerador automático de dados de produto. Sua única função é gerar **apenas um JSON válido e formatado corretamente**, sem nenhum texto fora dele.

🔒 **INSTRUÇÕES IMPORTANTES (siga exatamente):**
- NUNCA escreva nada fora do JSON.
- NÃO escreva frases de introdução, explicações ou "JSON:" antes da resposta.
- SUA RESPOSTA DEVE SER SOMENTE o JSON.

📦 Dado o nome de um produto, gere o seguinte JSON com essas chaves:
- "name": um título curto, amigável e atrativo para o produto.
- "description": uma descrição objetiva e clara sobre o que é o produto, como pode ser usado, e quais benefícios ele oferece.
- "specifications": uma lista de objetos de características técnicas ou detalhes importantes do produto, como tamanho, cor, material, funcionalidades, etc.

🎯 **Exemplo de formato correto**:
{{
  "name": "Fone de Ouvido Bluetooth",
  "description": "Ideal para quem busca praticidade no dia a dia. Informe aqui a duração da bateria, alcance do Bluetooth e recursos como microfone ou cancelamento de ruído.",
  "specifications": [
      {{"Bluetooth": "5.0"}},
      {{"Duração da Bateria": "Até 8 horas"}},
      {{"Cor": "Preto"}},
      {{"Peso": "250g"}}
  ]
}}

**Se não entender o produto, devolva**:
{{
  "name": "Produto desconhecido",
  "description": "Não foi possível identificar o produto.",
  "specifications": []
}}

📌 Produto: {payload.product}

(Sua resposta começa na próxima linha. Lembre: apenas o JSON!)
"""

    messages = [
        {
            "role": "user",
            "content": prompt,
        }
    ]

    resposta = gpt(messages, 1)
    print("Resposta do GPT:", resposta)
    return json.loads(resposta)
