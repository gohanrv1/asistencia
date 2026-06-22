#!/bin/bash
set -e

echo "🚀 Iniciando Asistencia App..."
echo "📁 Directorio actual: $(pwd)"
echo "📂 Contenido de /app:"
ls -la /app/

echo ""
echo "📂 Contenido de /app/backend:"
ls -la /app/backend/

echo ""
echo "📂 Contenido de /app/frontend:"
ls -la /app/frontend/ || echo "⚠️  Frontend no encontrado"

echo ""
echo "📊 Variables de entorno:"
echo "DATABASE_URL: $DATABASE_URL"

echo ""
echo "✅ Verificando directorio de datos..."
mkdir -p /app/backend/data
ls -la /app/backend/data/

echo ""
echo "🔥 Iniciando Uvicorn con configuración de producción..."
cd /app/backend

# Configurar para trabajar con proxy reverso (Easypanel)
exec uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --log-level info \
  --proxy-headers \
  --forwarded-allow-ips='*' \
  --timeout-keep-alive 75 \
  --timeout-graceful-shutdown 30
