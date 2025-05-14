from fastapi import FastAPI
from app.services.identify_image import identify_image
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import base64


class ImageUpload(BaseModel):
    image: str
    
class Chat(BaseModel):
    image: str = None
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
    
@app.get("/chat")
def chat(payload: Chat):
    if payload.image:
        image_bytes = base64.b64decode(payload.image)
        image = identify_image(image_bytes)[0]["classe"]
    return {"response": f"a imagem é {image} e a pergunta é {payload.prompt}"}