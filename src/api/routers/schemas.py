from pydantic import BaseModel, EmailStr
from typing import List


class Email(BaseModel):
    message_id: str
    sender_email: EmailStr
    is_readed: bool
    message_snippet: str
    subject: str

class EmailResponse(BaseModel):
    success: bool
    emails: List[Email]