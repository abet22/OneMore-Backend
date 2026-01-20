from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# --- SCHEMAS DE ITEMS ---

class ItemBase(BaseModel):
    title: str
    # Añadimos description aquí o en ItemCreate, pero es útil tenerla base
    description: str | None = None 

class ItemCreate(ItemBase):
    # Aquí es donde el usuario decide si es secreto al crearlo
    is_hidden: bool = False 

class ItemUpdate(BaseModel):
    title: str | None = None
    description: str | None = None # Permitimos editar la descripción
    count: int | None = None
    is_hidden: bool | None = None # Permitimos cambiar la privacidad

class ItemLog(BaseModel):
    id: int
    timestamp: datetime
    class Config:
        from_attributes = True

class Item(ItemBase):
    id: int
    count: int
    owner_id: int
    is_hidden: bool # El frontend necesita saber si pintar el candado 🔒
    
    class Config:
        from_attributes = True

# --- SCHEMAS DE USUARIOS ---
# (Esto se queda igual que lo tenías)
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