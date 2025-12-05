from pydantic import BaseModel

class UserMailModel(BaseModel):
    email: str
