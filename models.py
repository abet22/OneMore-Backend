from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
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
    title = Column(String, index=True)
    count = Column(Integer, default=0)
    owner_id = Column(Integer, ForeignKey("users.id"))

    # Relación: Un item pertenece a un usuario
    owner = relationship("User", back_populates="items")
    
    # NUEVO: Relación con el historial
    # cascade="all, delete" significa que si borras el item, se borra su historial
    logs = relationship("ItemLog", back_populates="item", cascade="all, delete")

class ItemLog(Base):
    __tablename__ = "item_logs"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # NUEVO: Relación de vuelta al Item (esto es lo que faltaba y daba el error)
    item = relationship("Item", back_populates="logs")