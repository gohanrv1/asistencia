# 📋 App de Asistencia

Aplicación web con soporte **offline/online**, proyectos, personas y eventos.  
Backend: **Python + FastAPI + SQLite** · Frontend: HTML puro (sin frameworks)

---

## 🚀 Instalación en VPS (Ubuntu/Debian)

### Paso 1 — Sube la carpeta al servidor

```bash
# Desde tu computador local:
scp -r asistencia/ usuario@IP_DEL_SERVIDOR:/opt/asistencia
```

### Paso 2 — Conéctate al servidor y ejecuta el instalador

```bash
ssh usuario@IP_DEL_SERVIDOR
cd /opt/asistencia
chmod +x instalar.sh
sudo bash instalar.sh
```

El script hace todo automáticamente:
- Instala dependencias Python
- Crea un entorno virtual
- Registra la app como servicio del sistema (inicia sola al reiniciar el servidor)

### Paso 3 — Abre la app

```
http://IP_DEL_SERVIDOR:8000
```

---

## 🔧 Instalación manual (sin el script)

```bash
cd asistencia/
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 📡 API REST

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/projects` | Listar proyectos |
| POST | `/api/projects` | Crear proyecto |
| DELETE | `/api/projects/{id}` | Eliminar proyecto |
| GET | `/api/projects/{id}/persons` | Listar personas del proyecto |
| POST | `/api/persons` | Crear persona |
| DELETE | `/api/persons/{id}` | Eliminar persona |
| GET | `/api/events` | Listar eventos (opcional: `?project_id=xxx`) |
| POST | `/api/events` | Crear evento |
| DELETE | `/api/events/{id}` | Eliminar evento |
| GET | `/api/events/{id}/attendance` | Ver asistencia de un evento |
| POST | `/api/events/{id}/attendance` | Guardar asistencia |
| POST | `/api/sync` | **Sincronizar cambios offline** |

Documentación interactiva (Swagger): `http://IP:8000/docs`

---

## 🔄 Cómo funciona el modo offline

1. El navegador guarda todo en **localStorage** como caché local.
2. Cuando no hay conexión, los cambios se acumulan en **"Pendientes"**.
3. Al recuperar la conexión, el botón **"Sincronizar ahora"** envía todo al servidor mediante `POST /api/sync`.
4. El servidor aplica los cambios en orden: proyectos → personas → eventos → asistencia.

---

## 🔐 Agregar contraseña (opcional)

Para proteger la app con usuario y contraseña, instala Nginx y configura autenticación básica:

```bash
apt install nginx apache2-utils -y
htpasswd -c /etc/nginx/.htpasswd admin
```

Luego crea `/etc/nginx/sites-available/asistencia`:

```nginx
server {
    listen 80;
    server_name TU_DOMINIO_O_IP;

    auth_basic "Asistencia";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
ln -s /etc/nginx/sites-available/asistencia /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

---

## 📁 Estructura del proyecto

```
asistencia/
├── backend/
│   ├── main.py           # API FastAPI + modelos SQLite
│   ├── requirements.txt  # Dependencias Python
│   └── asistencia.db     # Base de datos (se crea sola)
├── frontend/
│   └── index.html        # App completa (offline + sync)
├── instalar.sh           # Script de instalación automática
└── README.md             # Este archivo
```

---

## 🛠 Comandos útiles

```bash
systemctl status asistencia     # Ver si está corriendo
systemctl restart asistencia    # Reiniciar
systemctl stop asistencia       # Detener
journalctl -u asistencia -f     # Ver logs en tiempo real
```
