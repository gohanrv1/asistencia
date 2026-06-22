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
echo "🔥 Iniciando Uvicorn..."
cd /app/backend
exec uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info
