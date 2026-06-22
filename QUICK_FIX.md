# ⚡ SOLUCIÓN RÁPIDA - Servidor se Cierra

## El Problema
Tu servidor se inicia correctamente pero se cierra inmediatamente sin procesar peticiones HTTP.

## La Causa
Easypanel/Docker necesita configuraciones específicas de proxy y timeouts que Uvicorn solo no maneja bien.

## ✅ Solución Aplicada

He configurado **Gunicorn + Uvicorn** que es mucho más robusto para producción.

## 🚀 Qué Hacer AHORA

### 1. Sube los cambios a Git:
```bash
cd asistencia/
git add .
git commit -m "Fix: Usar Gunicorn para producción"
git push
```

### 2. En Easypanel:
- Ve a tu proyecto "asistencia"
- Click en **"Rebuild"**
- Espera a que termine

### 3. Verifica los nuevos logs:
Deberías ver:
```
🚀 Iniciando Asistencia App con Gunicorn...
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:8000
[INFO] Using worker: uvicorn.workers.UvicornWorker
```

**Y el servidor NO debe cerrarse** 🎉

### 4. Prueba la aplicación:
```
https://electo-asistencia.fxtfoe.easypanel.host/health
```

Debe responder:
```json
{
  "status": "ok",
  "service": "asistencia",
  "timestamp": "2026-06-22T..."
}
```

### 5. Abre la app:
```
https://electo-asistencia.fxtfoe.easypanel.host/
```

## 📊 Cambios Realizados

✅ Agregado **Gunicorn** a requirements.txt  
✅ Creado **gunicorn.conf.py** con configuración optimizada  
✅ Creado **start-gunicorn.sh** con 2 workers  
✅ Modificado **Dockerfile** para usar Gunicorn por defecto  
✅ Agregados **eventos de startup/shutdown** en FastAPI  
✅ Mejorado **health check** con timestamp  
✅ Configurado **proxy headers** y **timeouts**  

## 🔧 Si Sigue Sin Funcionar

**Opción 1:** Vuelve a Uvicorn simple
En [Dockerfile](Dockerfile), cambia la última línea a:
```dockerfile
CMD ["/app/start.sh"]
```

**Opción 2:** Verifica la configuración de Easypanel
- Health Check Path: `/health`
- Port: `8000`
- Restart Policy: `Unless Stopped`

**Opción 3:** Prueba localmente
```bash
docker-compose build
docker-compose up
```

Si funciona local pero no en Easypanel, es problema de configuración del servicio.

## 📁 Archivos Modificados

- `Dockerfile` - Usa Gunicorn por defecto
- `backend/requirements.txt` - Agrega Gunicorn
- `backend/main.py` - Eventos de startup y logs mejorados
- `start.sh` - Uvicorn con proxy headers
- `start-gunicorn.sh` - **NUEVO** - Script con Gunicorn
- `gunicorn.conf.py` - **NUEVO** - Configuración de Gunicorn

## 📖 Documentación Completa

- **[SOLUTION.md](SOLUTION.md)** - Solución detallada paso a paso
- **[EASYPANEL_DEPLOY.md](EASYPANEL_DEPLOY.md)** - Guía de despliegue
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Problemas comunes

---

**TL;DR:** Haz git push → Rebuild en Easypanel → Debería funcionar ✅
