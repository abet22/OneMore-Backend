# 1. AÑADIDO: 'Boolean' a los imports
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    display_name = Column(String)

    items = relationship("Item", back_populates="owner")

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    
    # 2. AÑADIDO: Campo para guardar el contenido secreto largo
    description = Column(String, nullable=True) 
    
    count = Column(Integer, default=0)
    owner_id = Column(Integer, ForeignKey("users.id"))
    position = Column(Integer, default=0)

    # 3. AÑADIDO: Flag para saber si hay que desencriptar al leer
    is_hidden = Column(Boolean, default=False) 

    owner = relationship("User", back_populates="items")
    
    # cascade="all, delete" para borrar logs si se borra el item
    logs = relationship("ItemLog", back_populates="item", cascade="all, delete")

class ItemLog(Base):
    __tablename__ = "item_logs"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    item = relationship("Item", back_populates="logs")