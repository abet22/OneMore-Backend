# Usamos una imagen ligera de Python
FROM python:3.11-slim

# Instalamos librerías del sistema necesarias para compilar cosas
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Carpeta de trabajo dentro del contenedor
WORKDIR /app

# Copiamos dependencias e instalamos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# El código lo montaremos como volumen en docker-compose, 
# así que no hace falta copiarlo aquí para desarrollo.
COPY . .

# Comando por defecto (lo sobrescribiremos en docker-compose)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]