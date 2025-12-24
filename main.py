from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from firebase_admin import auth, credentials
import firebase_admin
import models, schemas
from database import engine, SessionLocal

# Crear tablas (OJO: Ver nota abajo sobre borrar la DB)
models.Base.metadata.create_all(bind=engine)

if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

app = FastAPI(title="OneMore API")

# Configuración CORS
origins = ["*"] # Para desarrollo dejamos entrar a todos

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

# --- FUNCIÓN NUEVA: OBTENER USUARIO ACTUAL DESDE EL TOKEN ---
# Esto sirve para proteger las rutas. Si el token es falso, no pasan.
def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Falta el token de autorización")
    
    try:
        # El frontend envía "Bearer <token>", quitamos el "Bearer "
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

# --- RUTAS DE ITEMS (NUEVO) ---

# 1. Obtener mis items
@app.get("/items", response_model=list[schemas.Item])
def read_items(current_user: models.User = Depends(get_current_user)):
    return current_user.items

# 2. Crear un item nuevo
@app.post("/items", response_model=schemas.Item)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Creamos el item y le asignamos el ID del usuario dueño
    new_item = models.Item(title=item.title, owner_id=current_user.id)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

# 3. Actualizar un contador (Sumar/Restar)
@app.put("/items/{item_id}", response_model=schemas.Item)
def update_item(
    item_id: int, 
    item_update: schemas.ItemUpdate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    # Buscamos el item
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()

    if not db_item:
        raise HTTPException(status_code=404, detail="Item no encontrado")

    # VERIFICACIÓN DE SEGURIDAD: ¿Es tuyo este item?
    if db_item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para tocar este item")

    # Actualizamos el contador
    db_item.count = item_update.count
    db.commit()
    db.refresh(db_item)
    return db_item

# 4. Borrar un contador (Ya que estamos, lo dejamos hecho)
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