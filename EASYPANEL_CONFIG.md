# ⚙️ Configuración Easypanel - IMPORTANTE

## El Problema

Tu servidor **INICIA CORRECTAMENTE** pero Easypanel lo **MATA con SIGTERM** porque:
1. El health check no está configurado correctamente
2. O no está configurado en absoluto
3. O el timeout es muy corto

## ✅ Configuración EXACTA para Easypanel

### 1. General Settings
```
Name: asistencia
Port: 8000
```

### 2. Health Check (MUY IMPORTANTE)
⚠️ **SIN ESTO, EASYPANEL MATA EL CONTENEDOR**

```
Enabled: YES
Path: /health
Port: 8000
Initial Delay: 15 segundos
Period: 30 segundos
Timeout: 10 segundos
Success Threshold: 1
Failure Threshold: 3
```

### 3. Environment Variables
```
DATABASE_URL=sqlite:////app/backend/data/asistencia.db
```

### 4. Volumes (Para persistir datos)
```
Host Path: ./data
Container Path: /app/backend/data
```

### 5. Restart Policy
```
Always
```

### 6. Resources (Opcional pero recomendado)
```
Memory Limit: 512MB
CPU Limit: 0.5
```

## 🔍 Cómo Verificar la Configuración

1. En Easypanel, ve a tu proyecto "asistencia"
2. Click en **Settings**
3. Verifica que **Health Check** esté **HABILITADO**
4. Si no está, ACTÍVALO con los valores de arriba
5. **Rebuild** el proyecto

## 🎯 Por Qué Se Cierra

Los logs muestran:
```
[INFO] Application startup complete.
[INFO] Handling signal: term  ← EASYPANEL MATA EL PROCESO AQUÍ
[INFO] Shutting down
```

Esto pasa cuando:
- ❌ No hay health check configurado
- ❌ El health check falla
- ❌ El timeout del health check es muy corto
- ❌ Easypanel no puede conectar al puerto

## ✅ Solución

**Opción 1: Configurar Health Check (RECOMENDADO)**

En Easypanel:
1. Settings → Health Check
2. Enable: ON
3. Path: `/health`
4. Initial Delay: `15`
5. Save y Rebuild

**Opción 2: Desactivar Health Check (temporal)**

Si quieres probar sin health check:
1. Settings → Health Check
2. Enable: OFF
3. Save y Rebuild

Pero esto NO es recomendado en producción.

**Opción 3: Usar un Puerto Diferente**

Si el puerto 8000 tiene conflictos:
1. En Dockerfile, cambia `EXPOSE 8000` a `EXPOSE 8080`
2. En todos los scripts, cambia `--port 8000` a `--port 8080`
3. En Easypanel Settings, cambia Port a `8080`

## 🧪 Cómo Probar Localmente

Para verificar que el contenedor funciona:

```bash
# Build
docker-compose build

# Run
docker-compose up

# En otra terminal, probar el health check
curl http://localhost:8000/health

# Debería responder:
# {"status":"ok","service":"asistencia","timestamp":"..."}

# Si funciona local pero no en Easypanel, es 100% problema de configuración
```

## 📊 Checklist de Debugging

- [ ] Health Check está habilitado en Easypanel
- [ ] Health Check path es `/health` (no `/api/health`)
- [ ] Initial Delay es al menos 15 segundos
- [ ] El puerto en Settings es 8000
- [ ] No hay otro servicio usando el puerto 8000
- [ ] El dominio está correctamente apuntado
- [ ] El build termina sin errores
- [ ] Los logs muestran "Application startup complete"
- [ ] El health check endpoint responde localmente

## 🆘 Si Sigue Sin Funcionar

**Contacta con Soporte de Easypanel** y diles:

> "Mi contenedor inicia correctamente (logs muestran 'Application startup complete') pero inmediatamente recibe SIGTERM y se cierra. Los logs muestran '[INFO] Handling signal: term'. El contenedor funciona localmente. Sospecho que el health check no está funcionando correctamente."

Adjunta:
- Los logs completos (los que me mostraste)
- Screenshot de tu configuración de Health Check
- Resultado de `curl http://localhost:8000/health` en local

---

## ⚡ ACCIÓN INMEDIATA

1. **Ve a Easypanel → Tu proyecto → Settings**
2. **Busca la sección "Health Check"**
3. **Actívalo si está desactivado**
4. **Configúralo con:**
   - Path: `/health`
   - Initial Delay: `15`
   - Period: `30`
5. **Save**
6. **Rebuild**
7. **Espera 30 segundos**
8. **Prueba la URL**

Si con esto no funciona, el problema puede ser de red/proxy en Easypanel y necesitas contactar su soporte.
