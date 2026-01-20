import sqlite3
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
# Importamos tus modelos para saber qué campos usar
from models import Base, User, Item, ItemLog 

# 1. Conexión a la base de datos NUEVA (Postgres)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ Error: No encuentro la variable DATABASE_URL")
    sys.exit(1)

pg_engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=pg_engine)
pg_session = SessionLocal()

# 2. Conexión a la base de datos VIEJA (SQLite)
# Nota: En docker-compose montamos el archivo como 'old_data.db'
SQLITE_PATH = "onemore.db" 

if not os.path.exists(SQLITE_PATH):
    print(f"❌ Error: No encuentro el archivo {SQLITE_PATH} dentro del contenedor.")
    print("Asegúrate de haber añadido el volumen en docker-compose.yml")
    sys.exit(1)

print(f"✅ Conectado a SQLite: {SQLITE_PATH}")
print(f"✅ Conectado a Postgres: {DATABASE_URL}")

sqlite_conn = sqlite3.connect(SQLITE_PATH)
sqlite_conn.row_factory = sqlite3.Row # Para acceder por nombre de columna
cursor = sqlite_conn.cursor()

def migrate():
    try:
        # --- 1. MIGRAR USUARIOS ---
        print("\n🚀 Migrando Usuarios...")
        users = cursor.execute("SELECT * FROM users").fetchall()
        for row in users:
            # Comprobamos si ya existe para no duplicar
            exists = pg_session.query(User).filter_by(id=row['id']).first()
            if not exists:
                new_user = User(
                    id=row['id'],
                    firebase_uid=row['firebase_uid'],
                    email=row['email'],
                    display_name=row['display_name']
                    # Si tienes más campos, añádelos aquí
                )
                pg_session.add(new_user)
        pg_session.commit()
        print(f"   Terminado ({len(users)} usuarios)")

        # --- 2. MIGRAR ITEMS ---
        print("🚀 Migrando Items...")
        items = cursor.execute("SELECT * FROM items").fetchall()
        for row in items:
            exists = pg_session.query(Item).filter_by(id=row['id']).first()
            if not exists:
                # Manejamos el campo 'position' por si en SQLite era NULL o no existía en filas viejas
                pos = row['position'] if 'position' in row.keys() and row['position'] is not None else 0
                
                new_item = Item(
                    id=row['id'],
                    title=row['title'],
                    count=row['count'],
                    position=pos,
                    owner_id=row['owner_id']
                )
                pg_session.add(new_item)
        pg_session.commit()
        print(f"   Terminado ({len(items)} items)")

        # --- 3. MIGRAR LOGS (HISTORIAL) ---
        print("🚀 Migrando Historial (Logs)...")
        # Primero verificamos si existe la tabla logs en sqlite (por si es nueva)
        try:
            logs = cursor.execute("SELECT * FROM item_logs").fetchall()
            for row in logs:
                exists = pg_session.query(ItemLog).filter_by(id=row['id']).first()
                if not exists:
                    new_log = ItemLog(
                        id=row['id'],
                        item_id=row['item_id'],
                        timestamp=row['timestamp']
                    )
                    pg_session.add(new_log)
            pg_session.commit()
            print(f"   Terminado ({len(logs)} logs)")
        except sqlite3.OperationalError:
            print("⚠️  No se encontró tabla de logs en SQLite (es normal si es antigua). Saltando.")

        # --- 4. RESETEAR CONTADORES (MUY IMPORTANTE) ---
        # Como hemos insertado IDs manualmente, Postgres "no sabe" cuál es el siguiente ID.
        # Tenemos que actualizar sus secuencias internas.
        print("\n🔧 Ajustando secuencias de IDs en Postgres...")
        
        # Ajustamos secuencia de users
        pg_session.execute(text("SELECT setval(pg_get_serial_sequence('users', 'id'), COALESCE(MAX(id), 1)) FROM users;"))
        # Ajustamos secuencia de items
        pg_session.execute(text("SELECT setval(pg_get_serial_sequence('items', 'id'), COALESCE(MAX(id), 1)) FROM items;"))
        # Ajustamos secuencia de logs
        pg_session.execute(text("SELECT setval(pg_get_serial_sequence('item_logs', 'id'), COALESCE(MAX(id), 1)) FROM item_logs;"))
        
        pg_session.commit()
        print("✅ Secuencias ajustadas.")
        print("\n🎉 ¡MIGRACIÓN COMPLETADA CON ÉXITO!")

    except Exception as e:
        pg_session.rollback()
        print(f"\n❌ Error durante la migración: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrate()