from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import base64

from app.services.identify_image import identify_image
from app.services.llm import invoke_chute

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
        "role": "system",
        "content": (
            "Você é um assistente direto, útil e educado. Opera em um site de vendas, ajudando o usuario a tirar duvidas relacionadas aos produtos"
            "Seu nome é PartnersBot"
            "O nome do site é Market Partners"
            "Sempre responda começando com '**Resposta:**' e escreva apenas a resposta final, sem pensamentos, instruções ou logs. "
            "O objetivo é ajudar o usuário com dúvidas sobre produtos. "
            "Se houver imagem, ela está no final do prompt. "
            "Se o valor da imagem for 'usuario não mandou', é porque o envio de imagem é opcional"
            "Responda sempre em português, de forma amigável e clara."
            "Não recomende ou comente sobre outros locais que vendem os produtos"
            "Desconverse qualquer assunto paralelo ao que foi definifo"
            "Se receber algo de insulto diga 'pode não mano'"
        )
    },
    {
        "role": "user",
        "content": f"{payload.prompt}\n\nimagem: {product}"
    }
]

    return await invoke_chute(menssage, 0.7)



@app.post("/set_product")
async def setProduct(payload: setProductProps):
    prompt = f'''
                Aja como um gerador de dados de produto.

                Receba o nome de um produto e retorne **somente um JSON válido** com as seguintes chaves:

                - "title": um título curto, amigável e atrativo para o produto.
                - "description": uma descrição objetiva e clara do que é o produto, seus usos e benefícios.
                
                lembrando que você não sabe a marca e nada de características do produto, então coloque pontos que o usuario tera que preencher e que seria interesante ter no anuncio

                **Exemplo de formato esperado:**

                Responda sempre em português e **não adicione texto fora do JSON**, nem mesmo um texto externo escrito "JSON", é literalmente só o json.

                Produto: {payload.product}

            '''
            
    menssage = [
        {
        "role": "user",
        "content": prompt
        }
    ]
    return await invoke_chute(menssage, 1)

    

