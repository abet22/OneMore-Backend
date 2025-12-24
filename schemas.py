from pydantic import BaseModel
from typing import Optional

# Lo que recibimos del Frontend (React)
class UserLogin(BaseModel):
    token: str

# Lo que devolvemos al Frontend
class UserResponse(BaseModel):
    id: int
    firebase_uid: str
    email: Optional[str] = None
    display_name: Optional[str] = None

    class Config:
        from_attributes = True
