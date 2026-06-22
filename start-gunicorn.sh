#!/bin/bash
set -e

echo "🚀 Iniciando Asistencia App con Gunicorn..."
echo "📁 Directorio actual: $(pwd)"
echo ""
echo "✅ Verificando directorios..."
ls -la /app/backend/ | head -5
ls -la /app/frontend/ | head -5

echo ""
echo "📊 Variables de entorno:"
echo "DATABASE_URL: $DATABASE_URL"

echo ""
echo "✅ Verificando directorio de datos..."
mkdir -p /app/backend/data
ls -la /app/backend/data/

echo ""
echo "🔥 Iniciando con Gunicorn + Uvicorn workers..."
cd /app/backend

# Usar Gunicorn con configuración del archivo (más limpio)
exec gunicorn main:app --config /app/gunicorn.conf.py
