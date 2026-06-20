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

# Crear el directorio para datos persistentes (SQLite)
RUN mkdir -p /app/backend/data

# Definir el puerto expuesto
EXPOSE 8000

# Cambiar al directorio de ejecución del backend
WORKDIR /app/backend

# Configurar variable de entorno por defecto para la base de datos (con persistencia en el volumen)
ENV DATABASE_URL=sqlite:////app/backend/data/asistencia.db

# Ejecutar la aplicación usando uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
