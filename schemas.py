from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# --- SCHEMAS DE ITEMS ---

class ItemBase(BaseModel):
    title: str

class ItemCreate(ItemBase):
    pass

# ESTA ES LA CLAVE DEL ERROR 422
class ItemUpdate(BaseModel):
    # Al poner "= None", decimos que no es obligatorio enviarlo
    title: str | None = None
    count: int | None = None

class ItemLog(BaseModel):
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

class Item(ItemBase):
    id: int
    count: int
    owner_id: int
    # No metemos los logs aquí para no sobrecargar la lista principal
    
    class Config:
        from_attributes = True

# --- SCHEMAS DE USUARIOS ---

class UserBase(BaseModel):
    email: str | None = None
    display_name: str | None = None

class UserLogin(BaseModel):
    token: str

class UserCreate(UserBase):
    firebase_uid: str

class UserResponse(UserBase):
    id: int
    firebase_uid: str
    items: List[Item] = []

    class Config:
        from_attributes = True