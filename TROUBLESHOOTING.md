# 🔧 Solución: Servidor se Cierra Inmediatamente

## Tu Problema Específico

Estás viendo estos logs:
```
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [1]
```

El servidor se inicia pero se cierra inmediatamente.

## Causas Comunes y Soluciones

### 1. **Easypanel no detecta que el servicio está corriendo**

**Solución implementada:**
- ✅ Agregado endpoint `/health` para health checks
- ✅ Agregado endpoint de fallback en la raíz `/`
- ✅ Mejorado el script de inicio con logs detallados

**Prueba esto:**
```bash
# Accede a los logs del contenedor en Easypanel
# Busca las líneas que empiezan con 🔍 y verifica:
# - ✅ Montando frontend desde /app/frontend
# - Si ves: ⚠️ Advertencia: No se encontró el directorio frontend
```

### 2. **El contenedor no tiene el frontend montado correctamente**

**Verificación:**
Accede a: `https://electo-asistencia.fxtfoe.easypanel.host/health`

Si responde con:
```json
{
  "status": "ok",
  "service": "asistencia"
}
```

Significa que el backend está corriendo. Ahora prueba:
`https://electo-asistencia.fxtfoe.easypanel.host/api/projects`

Debe responder con: `[]` (array vacío)

### 3. **Easypanel está matando el proceso**

**En la configuración de Easypanel:**

1. Ve a tu proyecto `asistencia`
2. En la pestaña **Settings**:
   - Asegúrate que el **Port** sea `8000`
   - En **Health Check**, configura:
     - Path: `/health`
     - Port: `8000`
     - Interval: `30s`

3. En **Environment Variables**, agrega:
   ```
   DATABASE_URL=sqlite:////app/backend/data/asistencia.db
   ```

4. En **Volumes** (MUY IMPORTANTE para persistencia):
   - Host Path: `./data`
   - Container Path: `/app/backend/data`

### 4. **El proceso no se mantiene en primer plano**

**Solución implementada:**
- ✅ El script `start.sh` usa `exec` para mantener el proceso principal
- ✅ Configurado con `--host 0.0.0.0` para aceptar conexiones externas

### 5. **Problemas con el repositorio Git**

Si estás desplegando desde Git:

**Verifica en Easypanel:**
- La rama correcta está seleccionada
- El directorio build es: `.` (raíz del repo)
- El Dockerfile path es: `./Dockerfile`

### 6. **Reiniciar desde cero**

En Easypanel:

1. **Detén el servicio**
2. **Elimina el contenedor**
3. **Limpia la caché de build**
4. **Reconstruye**:
   - Settings → General → Rebuild

### 7. **Prueba local primero**

Antes de desplegar en Easypanel, prueba localmente:

```bash
# En tu computadora
cd asistencia/

# Construir
docker-compose build

# Iniciar
docker-compose up

# Deberías ver:
# 🚀 Iniciando Asistencia App...
# 📁 Directorio actual: /app
# ✅ Verificando directorio de datos...
# 🔥 Iniciando Uvicorn...
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

Si ves eso y NO se cierra, entonces el problema es de configuración en Easypanel.

Abre en tu navegador: `http://localhost:8000`

### 8. **Comandos de Debugging**

Si tienes acceso SSH al servidor de Easypanel:

```bash
# Ver logs en tiempo real
docker logs -f app-asistencia

# Ver si el contenedor está corriendo
docker ps -a | grep asistencia

# Entrar al contenedor
docker exec -it app-asistencia /bin/bash

# Dentro del contenedor, verifica:
ls -la /app/frontend/
cat /app/frontend/index.html
```

## ✅ Checklist de Verificación

- [ ] El puerto 8000 está configurado en Easypanel
- [ ] El health check path es `/health`
- [ ] El volumen para datos está configurado
- [ ] El repositorio Git tiene todos los archivos
- [ ] Los archivos `Dockerfile`, `start.sh`, y `.dockerignore` existen
- [ ] El directorio `frontend/` con `index.html` existe
- [ ] El directorio `backend/` con `main.py` existe
- [ ] Prueba local funciona correctamente

## 🆘 Si Nada Funciona

**Opción 1: Despliegue simple sin Docker**

En Easypanel, usa un servicio de Python directamente:
- Type: Python
- Start command: `cd backend && uvicorn main:app --host 0.0.0.0 --port 8000`
- Requirements: `backend/requirements.txt`

**Opción 2: Usa el servidor alternativo**

Hay una carpeta `server/` con una versión más simple. Cámbiala en el Dockerfile:

```dockerfile
# En lugar de
COPY backend/ /app/backend/
# Usa
COPY server/ /app/backend/
```

**Opción 3: Contacta con Easypanel**

Los logs que compartiste sugieren que el proceso se inicia correctamente pero algo lo está deteniendo. Esto podría ser:
- Un problema de configuración de proxy en Easypanel
- Un health check fallido
- Límites de recursos

Contacta con soporte de Easypanel mostrándoles estos logs.

---

## 📞 Próximos Pasos

1. **Aplica los cambios**: Los archivos ya fueron actualizados con las mejoras
2. **Sube a Git**: Haz commit y push de los cambios
3. **Rebuil en Easypanel**: Reconstruye el proyecto
4. **Verifica logs**: Revisa los nuevos logs que incluyen los emojis 🔍 ✅ ⚠️
5. **Prueba /health**: Accede a `/health` para verificar que responde

Si después de esto sigue sin funcionar, copia los nuevos logs completos y los revisamos.
