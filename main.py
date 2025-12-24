from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from firebase_admin import auth, credentials
import firebase_admin
import models, schemas
from database import engine, SessionLocal
from models import Base, User, Item, ItemLog 

# models.Base.metadata.create_all(bind=engine) Ahora usamos migraciones Alembic

if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

app = FastAPI(title="OneMore API")

# Configuración CORS
origins = ["*"] 

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependencia de Base de Datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Obtener usuario actual
def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Falta el token de autorización")
    
    try:
        token = authorization.split(" ")[1]
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    user = db.query(models.User).filter(models.User.firebase_uid == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en BD")
    return user

# --- RUTAS ---

@app.get("/")
def read_root():
    return {"mensaje": "API OneMore v1.0"}

@app.post("/login", response_model=schemas.UserResponse)
def login_user(user_input: schemas.UserLogin, db: Session = Depends(get_db)):
    try:
        decoded_token = auth.verify_id_token(user_input.token)
        uid = decoded_token['uid']
        email = decoded_token.get('email')
        name = decoded_token.get('name')
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Error token: {str(e)}")

    db_user = db.query(models.User).filter(models.User.firebase_uid == uid).first()
    if db_user:
        return db_user
    
    new_user = models.User(firebase_uid=uid, email=email, display_name=name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# --- RUTAS DE ITEMS ---

@app.get("/items", response_model=list[schemas.Item])
def read_items(current_user: models.User = Depends(get_current_user)):
    return current_user.items

@app.post("/items", response_model=schemas.Item)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    new_item = models.Item(title=item.title, owner_id=current_user.id)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

# --- NUEVA RUTA ESPECIAL: SUMAR Y REGISTRAR TIEMPO ---
# Úsala en el botón "+1" del frontend en lugar del PUT genérico
@app.post("/items/{item_id}/increment", response_model=schemas.Item)
def increment_item(item_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # 1. Buscar el item y verificar dueño
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    
    if db_item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso")

    # 2. Sumar 1 al contador
    db_item.count += 1
    
    # 3. GUARDAR EL REGISTRO (TIMESTAMP)
    new_log = models.ItemLog(item_id=db_item.id)
    db.add(new_log)
    
    # 4. Confirmar cambios
    db.commit()
    db.refresh(db_item)
    return db_item

# --- (Opcional) EDITAR MANUALMENTE ---
# Esta la dejamos por si quieres editar el nombre o resetear el contador a 0
@app.put("/items/{item_id}", response_model=schemas.Item)
def update_item(
    item_id: int, 
    item_update: schemas.ItemUpdate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    if db_item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso")

    # Aquí actualizamos lo que venga (titulo o count) pero SIN crear log
    # Útil para correcciones manuales
    if item_update.title:
        db_item.title = item_update.title
    if item_update.count is not None:
        db_item.count = item_update.count
        
    db.commit()
    db.refresh(db_item)
    return db_item

@app.delete("/items/{item_id}")
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    if db_item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="No es tu item")

    db.delete(db_item)
    db.commit()
    return {"mensaje": "Borrado"}

# --- NUEVA RUTA: RESTAR Y BORRAR ÚLTIMO REGISTRO ---
@app.post("/items/{item_id}/decrement", response_model=schemas.Item)
def decrement_item(item_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    
    if not db_item:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    if db_item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso")

    # Solo restamos si es mayor que 0
    if db_item.count > 0:
        db_item.count -= 1
        
        # TRUCO DE MAGIA: Buscamos el último log de este item y lo borramos
        # Así las gráficas de tiempo serán 100% reales.
        last_log = db.query(models.ItemLog)\
            .filter(models.ItemLog.item_id == item_id)\
            .order_by(models.ItemLog.timestamp.desc())\
            .first()
            
        if last_log:
            db.delete(last_log)
            
        db.commit()
        db.refresh(db_item)
    
    return db_item

# --- NUEVA RUTA: OBTENER HISTORIAL DE UN ITEM ---
@app.get("/items/{item_id}/logs")
def get_item_logs(item_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # 1. Verificar que el item existe y es tuyo
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    if db_item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso")

    # 2. Obtener los logs ordenados por fecha (el más reciente primero)
    logs = db.query(models.ItemLog)\
             .filter(models.ItemLog.item_id == item_id)\
             .order_by(models.ItemLog.timestamp.desc())\
             .all()
    
    return logs