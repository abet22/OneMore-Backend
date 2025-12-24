from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

# Esta es la base de la que heredarán nuestros modelos
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # Aquí guardaremos el ID que nos da Google/Firebase (ej: 'dKz2...')
    firebase_uid = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True)
    display_name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relación: Un usuario tiene muchos Items
    items = relationship("Item", back_populates="owner")

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True) # Ej: "Cervezas", "Libros"
    color = Column(String, default="#3B82F6") # Un azul por defecto
    icon = Column(String, nullable=True) # Ej: "🍺"
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Clave foránea: A qué usuario pertenece esto
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Relaciones
    owner = relationship("User", back_populates="items")
    entries = relationship("Entry", back_populates="item")

class Entry(Base):
    __tablename__ = "entries"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Integer, default=1) # Por si quieres sumar de 2 en 2
    timestamp = Column(DateTime(timezone=True), server_default=func.now()) # CUANDO ocurrió
    
    # Clave foránea: A qué Item pertenece este clic
    item_id = Column(Integer, ForeignKey("items.id"))
    
    # Relación
    item = relationship("Item", back_populates="entries")
