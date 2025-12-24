from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    display_name = Column(String)

    # Relación: Un usuario tiene muchos items
    items = relationship("Item", back_populates="owner")

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)  # Ej: "Cervezas 2024"
    count = Column(Integer, default=0)  # Ej: 5
    owner_id = Column(Integer, ForeignKey("users.id")) # Dueño del contador

    # Relación: Un item pertenece a un dueño
    owner = relationship("User", back_populates="items")