import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    # Si no hay clave, generamos una por defecto para que no explote, 
    # pero lo ideal es tenerla en el .env
    ENCRYPTION_KEY = Fernet.generate_key().decode()

cipher_suite = Fernet(ENCRYPTION_KEY.encode())

def encrypt_text(text: str) -> str:
    if not text:
        return text
    return cipher_suite.encrypt(text.encode()).decode()

def decrypt_text(text: str) -> str:
    if not text:
        return text
    try:
        return cipher_suite.decrypt(text.encode()).decode()
    except Exception:
        # Si falla la desencriptación (ej. texto no encriptado), devolvemos el original
        return text
