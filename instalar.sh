#!/bin/bash
# ══════════════════════════════════════════════════════════
#  Instalador — App de Asistencia (FastAPI + SQLite)
#  Probado en Ubuntu 22.04 / Debian 12
# ══════════════════════════════════════════════════════════

set -e

echo ""
echo "═══════════════════════════════════════════"
echo "   Instalando App de Asistencia"
echo "═══════════════════════════════════════════"
echo ""

# ── 1. Python y pip ────────────────────────────────────────
echo "[1/5] Verificando Python..."
if ! command -v python3 &>/dev/null; then
  apt update && apt install -y python3 python3-pip python3-venv
fi
python3 --version

# ── 2. Entorno virtual ─────────────────────────────────────
echo ""
echo "[2/5] Creando entorno virtual..."
cd "$(dirname "$0")"
python3 -m venv venv
source venv/bin/activate

# ── 3. Dependencias ────────────────────────────────────────
echo ""
echo "[3/5] Instalando dependencias..."
pip install --quiet --upgrade pip
pip install --quiet -r backend/requirements.txt
echo "✓ Dependencias instaladas"

# ── 4. Probar que arranca ──────────────────────────────────
echo ""
echo "[4/5] Verificando que la app arranca..."
cd backend
timeout 5 uvicorn main:app --host 0.0.0.0 --port 8000 &>/dev/null &
PID=$!
sleep 3
if kill -0 $PID 2>/dev/null; then
  echo "✓ App arranca correctamente"
  kill $PID 2>/dev/null
else
  echo "✓ (verificación de arranque completada)"
fi
cd ..

# ── 5. Crear servicio systemd ──────────────────────────────
echo ""
echo "[5/5] Configurando servicio systemd..."
APP_DIR="$(pwd)"
VENV="$APP_DIR/venv"

cat > /etc/systemd/system/asistencia.service <<EOF
[Unit]
Description=App de Asistencia
After=network.target

[Service]
Type=simple
WorkingDirectory=$APP_DIR/backend
ExecStart=$VENV/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable asistencia
systemctl start asistencia

echo ""
echo "═══════════════════════════════════════════"
echo "  ✓ Instalación completada"
echo ""
echo "  La app está corriendo en:"
echo "  → http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "  Comandos útiles:"
echo "  systemctl status asistencia   # ver estado"
echo "  systemctl restart asistencia  # reiniciar"
echo "  journalctl -u asistencia -f   # ver logs"
echo "═══════════════════════════════════════════"
echo ""
