# 🔧 SOLUCIÓN DEFINITIVA: Servidor se Cierra Inmediatamente

## Tu Problema

El servidor se inicia perfectamente pero se cierra sin razón aparente:
- ✅ Todos los directorios existen
- ✅ Frontend se monta correctamente  
- ✅ Uvicorn inicia en 0.0.0.0:8000
- ❌ Se cierra inmediatamente sin peticiones HTTP

## Causa Raíz

**Easypanel está detrás de un proxy reverso** y necesita:
1. Headers de proxy configurados correctamente
2. Timeouts adecuados
3. Configuración de workers robusta

## ✅ SOLUCIÓN APLICADA

He actualizado el proyecto con **dos métodos de inicio**:

### Método 1: Uvicorn con proxy headers (actual)
```bash
# start.sh ahora incluye:
uvicorn main:app \
  --proxy-headers \
  --forwarded-allow-ips='*' \
  --timeout-keep-alive 75
```

### Método 2: Gunicorn + Uvicorn workers (más robusto)
```bash
# start-gunicorn.sh (RECOMENDADO para producción)
gunicorn main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 2 \
  --timeout 120
```

## 🚀 CÓMO APLICAR LA SOLUCIÓN

### Opción A: Usar Gunicorn (RECOMENDADO)

**Paso 1:** Modifica el [Dockerfile](Dockerfile) - cambia la última línea:

```dockerfile
# Cambiar de:
CMD ["/app/start.sh"]

# A:
CMD ["/app/start-gunicorn.sh"]
```

**Paso 2:** Rebuild en Easypanel

**Paso 3:** Los nuevos logs deberían mostrar:
```
🔥 Iniciando con Gunicorn + Uvicorn workers...
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:8000
[INFO] Using worker: uvicorn.workers.UvicornWorker
```

Y el servidor **NO debería cerrarse**.

### Opción B: Usar Uvicorn mejorado

Si prefieres no usar Gunicorn, los cambios en `start.sh` ya están aplicados:
- ✅ `--proxy-headers`
- ✅ `--forwarded-allow-ips='*'`  
- ✅ `--timeout-keep-alive 75`

Simplemente haz rebuild y prueba.

## 📋 Configuración en Easypanel

Asegúrate de tener estas configuraciones:

**Health Check:**
- Path: `/health`
- Port: `8000`
- Initial Delay: `10` segundos
- Period: `30` segundos
- Timeout: `5` segundos

**Environment Variables:**
```
DATABASE_URL=sqlite:////app/backend/data/asistencia.db
```

**Port Mapping:**
```
Container Port: 8000
```

**Restart Policy:**
```
Unless Stopped
```

## 🧪 Prueba Local

Antes de desplegar, prueba localmente:

**Con Uvicorn:**
```bash
docker-compose build
docker-compose up
```

**Con Gunicorn:**
```bash
docker-compose build
docker run -p 8000:8000 app-asistencia /app/start-gunicorn.sh
```

En ambos casos, el servidor debe:
1. ✅ Iniciar correctamente
2. ✅ Mostrar logs con emojis
3. ✅ **NO cerrarse**
4. ✅ Responder en `http://localhost:8000/health`

## 🎯 Diferencias Entre los Métodos

| Característica | Uvicorn | Gunicorn+Uvicorn |
|----------------|---------|------------------|
| Simplicidad | ✅ Más simple | ⚠️ Más complejo |
| Estabilidad en producción | ⚠️ Buena | ✅ Excelente |
| Manejo de workers | ❌ Single worker | ✅ Multiple workers |
| Recuperación de errores | ⚠️ Básica | ✅ Avanzada |
| Zero-downtime deploys | ❌ No | ✅ Sí |
| **Recomendado para** | Desarrollo | **Producción** |

## 🔍 Debugging Adicional

Si sigue sin funcionar, verifica en los logs:

**Busca estas líneas:**
```
✅ Esquema de base de datos OK
🚀 Aplicación FastAPI iniciada correctamente
```

**Si ves errores de base de datos:**
```
❌ Error al crear tablas: ...
```

Entonces el problema es con SQLite. Verifica que el volumen esté configurado correctamente:
```
Host: ./data
Container: /app/backend/data
```

## 📝 Checklist Final

- [ ] Gunicorn agregado a requirements.txt
- [ ] gunicorn.conf.py copiado al contenedor
- [ ] start-gunicorn.sh creado y con permisos ejecutables
- [ ] Dockerfile actualizado para copiar nuevos archivos
- [ ] CMD en Dockerfile apunta a start-gunicorn.sh
- [ ] Rebuild del contenedor
- [ ] Health check configurado en Easypanel
- [ ] Logs muestran "Listening at: http://0.0.0.0:8000"
- [ ] Servidor NO se cierra automáticamente
- [ ] /health responde correctamente

## 🆘 Si Aún No Funciona

**Verifica en los logs de Easypanel:**

1. ¿Ves "Listening at: http://0.0.0.0:8000"?
   - ✅ Sí → El servidor inicia
   - ❌ No → Hay un error de Python

2. ¿Ves peticiones HTTP en los logs?
   - ✅ Sí → Easypanel está haciendo health checks
   - ❌ No → Easypanel no puede conectar al contenedor

3. ¿El contenedor se mantiene corriendo?
   ```bash
   docker ps | grep asistencia
   ```
   - ✅ Sí → Problema de red/proxy
   - ❌ No → Problema de configuración

**Contacta soporte de Easypanel con:**
- Los logs completos (con los emojis)
- La configuración de tu servicio (screenshot)
- Esta información: "Servidor inicia pero se cierra inmediatamente, sin peticiones HTTP"

## 📞 Próximos Pasos

1. ✅ Cambiar Dockerfile para usar start-gunicorn.sh
2. ✅ Hacer git commit y push
3. ✅ Rebuild en Easypanel  
4. ✅ Ver nuevos logs (deberían mostrar Gunicorn)
5. ✅ Verificar que el servidor se mantiene corriendo
6. ✅ Probar https://electo-asistencia.fxtfoe.easypanel.host/health

Si funciona, verás:
```json
{
  "status": "ok",
  "service": "asistencia",
  "timestamp": "2026-06-22T16:59:00.000000"
}
```
