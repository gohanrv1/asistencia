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

# Usar Gunicorn con workers de Uvicorn para mejor estabilidad
exec gunicorn main:app \
  --config /app/gunicorn.conf.py \
  --bind 0.0.0.0:8000 \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --timeout 120 \
  --keepalive 5 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
