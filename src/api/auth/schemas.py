from pydantic import BaseModel, Field, field_validator
import re

class UserModel(BaseModel):
    
    email:str
    password:str
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise ValueError("Email format is invalid !!")
        return value
    
    
class TokenRefreshRequest(BaseModel):
    refresh_token: str = Field(..., example="your.jwt.refresh.token", description="Valid refresh token")