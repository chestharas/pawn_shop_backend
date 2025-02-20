from pydantic import BaseModel

class UserToken(BaseModel):
    phone_number: str
    password: str