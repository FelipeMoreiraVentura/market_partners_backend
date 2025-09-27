from openai import BaseModel


class Chat(BaseModel):
    image: str
    prompt: str
    history: str
