import base64
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.chat import chatRoute
from app.routes.set_product import setProductRoute
from app.schemas.chat import Chat
from app.schemas.image_upload import ImageUpload
from app.schemas.set_product import setProductProps
from app.services.identify_image import identify_image

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
    return chatRoute(payload=payload)

@app.post("/set_product")
async def setProduct(payload: setProductProps):
    return setProductRoute(payload=payload)
