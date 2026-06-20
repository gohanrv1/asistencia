#!/usr/bin/env bash
# ────────────────────────────────────────────────────────────
# start.sh — Instala dependencias y arranca el servidor
# Uso: bash start.sh
# ────────────────────────────────────────────────────────────
set -e

echo "📦 Instalando dependencias..."
pip install -r requirements.txt

echo ""
echo "✅ Listo. Arrancando servidor en http://0.0.0.0:8000"
echo "   Presiona Ctrl+C para detener."
echo ""

# Cambia API_KEY por tu clave secreta real
export API_KEY="${API_KEY:-cambia_esta_clave_secreta}"

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
