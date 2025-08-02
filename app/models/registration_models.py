
from pydantic import BaseModel


class RegisterRequest(BaseModel):
    user_id: str
    email : str
    username : str


class Token(BaseModel):
    access_token: str
    token_type: str