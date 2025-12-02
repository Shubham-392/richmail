from pydantic import BaseModel, Field
import re

class UserMailModel(BaseModel):
    email: str
