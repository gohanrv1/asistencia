# Usar una imagen oficial de Python como base
FROM python:3.11-slim

# Evitar que Python escriba archivos .pyc y forzar salida de logs sin buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Crear directorio de la aplicación
WORKDIR /app

# Copiar archivo de requerimientos
COPY backend/requirements.txt /app/backend/requirements.txt

# Actualizar pip e instalar dependencias de Python
# Se fuerza la actualización de sqlalchemy y pydantic para compatibilidad moderna
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt && \
    pip install --no-cache-dir --upgrade sqlalchemy pydantic

# Copiar el código del backend y del frontend
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/
COPY start.sh /app/start.sh
COPY start-gunicorn.sh /app/start-gunicorn.sh
COPY gunicorn.conf.py /app/gunicorn.conf.py

# Hacer ejecutables los scripts de inicio
RUN chmod +x /app/start.sh /app/start-gunicorn.sh

# Crear el directorio para datos persistentes (SQLite)
RUN mkdir -p /app/backend/data

# Definir el puerto expuesto
EXPOSE 8000

# Configurar variable de entorno por defecto para la base de datos (con persistencia en el volumen)
ENV DATABASE_URL=sqlite:////app/backend/data/asistencia.db

# Usar Gunicorn para mayor estabilidad en producción
# Para usar Uvicorn simple, cambia a: CMD ["/app/start.sh"]
CMD ["/app/start-gunicorn.sh"]
