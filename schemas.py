from pydantic import BaseModel
from typing import List, Optional

# --- SCHEMAS DE ITEMS (CONTADORES) ---
class ItemBase(BaseModel):
    title: str

class ItemCreate(ItemBase):
    pass

# Clase para recibir actualizaciones de contador
class ItemUpdate(BaseModel):
    count: int

class Item(ItemBase):
    id: int
    count: int
    owner_id: int

    class Config:
        from_attributes = True

# --- SCHEMAS DE USUARIOS ---
class UserLogin(BaseModel):
    token: str

class UserResponse(BaseModel):
    id: int
    firebase_uid: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    items: List[Item] = [] # Ahora el usuario devolverá también sus items

    class Config:
        from_attributes = True