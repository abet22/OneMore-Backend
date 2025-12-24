from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware # <--- 1. Importante
from sqlalchemy.orm import Session
from firebase_admin import auth, credentials
import firebase_admin
import models, schemas
from database import engine, SessionLocal

# Crear tablas
models.Base.metadata.create_all(bind=engine)

# Inicializar Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

app = FastAPI(title="OneMore API")

# --- 2. CONFIGURACIÓN CORS (ESTO ES LO QUE ARREGLA EL 404) ---
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://192.168.1.115:5173", # Tu Raspberry
    "http://192.168.1.114:5173",
    "*" # Permitir todo (para desarrollo es lo más fácil)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,    # Qué IPs pueden hablar con el server
    allow_credentials=True,
    allow_methods=["*"],      # Permitir GET, POST, OPTIONS, etc.
    allow_headers=["*"],
)
# -------------------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"mensaje": "¡OneMore backend online!"}

@app.post("/login", response_model=schemas.UserResponse)
def login_user(user_input: schemas.UserLogin, db: Session = Depends(get_db)):
    # Verificar token
    try:
        decoded_token = auth.verify_id_token(user_input.token)
        uid = decoded_token['uid']
        email = decoded_token.get('email')
        name = decoded_token.get('name')
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")

    # Buscar o Crear Usuario
    db_user = db.query(models.User).filter(models.User.firebase_uid == uid).first()

    if db_user:
        return db_user
    else:
        new_user = models.User(firebase_uid=uid, email=email, display_name=name)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
