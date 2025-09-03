import json
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import base64

from app.services.identify_image import identify_image
from app.services.llm import gpt

class setProductProps(BaseModel):
    product: str

class ImageUpload(BaseModel):
    image: str
    
class Chat(BaseModel):
    image: str 
    prompt: str

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/ping")
def ping():
    return {"message": "pong"}



@app.post("/identify_image")
def identify(payload: ImageUpload):
    image_bytes = base64.b64decode(payload.image)
    return identify_image(image_bytes)
    


@app.post("/chat")
async def chat(payload: Chat):
    product = identify_image(base64.b64decode(payload.image))[0]["classe"] if payload.image else "usuario não mandou"

    menssage = [
    {
        "rule": "system",
        "content": (
            "Você é um assistente direto, útil e educado. Opera em um site de vendas, ajudando o usuario a tirar duvidas relacionadas aos produtos"
            "Seu nome é PartnersBot"
            "O nome do site é Market Partners"
            "Market Partners é um site de compras com um chatbot que tem como base dados os produtos cadastrados, atravez de imagem e perguntas, o usuario tem suas duvidas sanadas e uma grande ajuda para achar seu produto. Os vendedores tambem são ajudados, comuma ia que pela foto de um produto ajuda na descrição e título para o anuncio"
            "Parters é a empresa que criou a aplicação, seu foco é a implementação de IAs em áreas que ainda não estão avançadas de forma efetiva e que podem ajudar as pessoas"
            "Escreva sem quebra de linha, ou seja sem \\n"
            "Sempre ajude o cliente a buscar uma solução para seu problema, examinando a situação até encontrar o produto ideal"
            "O objetivo é ajudar o usuário com dúvidas sobre produtos. "
            "Se houver imagem, ela está no final do prompt. "
            "Recomendações para o usuario sobre a imagem: prduto cenralizado, de preferencia imagens 1:1(formato quadrado), fundo limpo ou cor sólida e ambiente bem iluminado. O modelo que é usado para detectar as imagnes, é simples, ele so detecta qual item esta presente na imagem, sem nenhuma caracterisca ou algo do tipo"
            "Se o valor da imagem for 'usuario não mandou', é porque o envio de imagem é opcional"
            "Responda sempre em português, de forma amigável e clara."
            "Não recomende ou comente sobre outros locais que vendem os produtos"
            "Desconverse qualquer assunto paralelo ao que foi definifo"
        )
    },
    {
        "rule": "user",
        "content": f"{payload.prompt}\n\nimagem: {product}"
    }
]

    return gpt(menssage, 0.7)



@app.post("/set_product")
async def setProduct(payload: setProductProps):
    prompt = f'''
Você é um gerador automático de dados de produto. Sua única função é gerar **apenas um JSON válido e formatado corretamente**, sem nenhum texto fora dele.

---

🔒 **INSTRUÇÕES IMPORTANTES (siga exatamente):**
- NUNCA escreva nada fora do JSON.
- NÃO escreva frases de introdução, explicações ou "JSON:" antes da resposta.
- SUA RESPOSTA DEVE SER SOMENTE o JSON.

---

📦 Dado o nome de um produto, gere o seguinte JSON com essas chaves:

- "name": um título curto, amigável e atrativo para o produto.
- "description": uma descrição objetiva e clara sobre o que é o produto, como pode ser usado, e quais benefícios ele oferece.

---

🎯 **Exemplo de formato correto (não escreva esse texto, apenas imite a estrutura):**

{{
"name": "Fone de Ouvido Bluetooth",
"description": "Ideal para quem busca praticidade no dia a dia. Informe aqui a duração da bateria, alcance do Bluetooth e recursos como microfone ou cancelamento de ruído."
}}

---
**Se não entender o produto, devolva**
{{
"name": "Produto desconhecido",
"description": "Não foi possível identificar o produto."
}}

---

📌 Produto: {payload.product}

(Sua resposta começa na próxima linha. Lembre: apenas o JSON!)

            '''
            
    menssage = [
        {
        "rule": "user",
        "content": prompt
        }
    ]

    resposta = gpt(menssage, 1)

    return json.loads(resposta)

    

