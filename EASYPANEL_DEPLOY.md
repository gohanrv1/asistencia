# 🚀 Despliegue en Easypanel

## Configuración para tu servidor

Tu aplicación está configurada para desplegarse en:
**https://electo-asistencia.fxtfoe.easypanel.host/**

## Pasos para desplegar en Easypanel:

### 1. Configuración del Proyecto

En Easypanel, crea un nuevo proyecto con estas configuraciones:

**General:**
- Nombre: `asistencia`
- Puerto: `8000`

**Build:**
- Dockerfile: Automático (usa el `Dockerfile` incluido)
- Build Context: `.`

**Domains:**
- Dominio: `electo-asistencia.fxtfoe.easypanel.host`

**Environment Variables:**
```
DATABASE_URL=sqlite:////app/backend/data/asistencia.db
```

**Volumes (Persistencia de Datos):**
```
Host Path: ./data
Container Path: /app/backend/data
```

### 2. Verificar el Despliegue

Después de desplegar, verifica que el servidor esté corriendo:

**Health Check:**
```
https://electo-asistencia.fxtfoe.easypanel.host/health
```

Debe responder:
```json
{
  "status": "ok",
  "service": "asistencia"
}
```

**Documentación API:**
```
https://electo-asistencia.fxtfoe.easypanel.host/docs
```

**Frontend (Página Principal):**
```
https://electo-asistencia.fxtfoe.easypanel.host/
```

### 3. Solución de Problemas

Si el contenedor se cierra inmediatamente:

1. **Verifica los logs:**
   ```bash
   docker logs app-asistencia
   ```

2. **Verifica que el frontend existe:**
   - Debe existir el directorio `frontend/` con `index.html`

3. **Verifica el health check:**
   ```bash
   curl http://localhost:8000/health
   ```

4. **Reconstruir el contenedor:**
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

### 4. Prueba Local antes de Desplegar

Para probar localmente antes de subir a Easypanel:

```bash
# Construir la imagen
docker-compose build

# Iniciar el contenedor
docker-compose up -d

# Ver los logs
docker-compose logs -f

# Probar en el navegador
# http://localhost:8000
```

### 5. Estructura de Archivos Necesarios

Asegúrate de tener esta estructura antes de desplegar:

```
asistencia/
├── backend/
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   └── index.html
├── docker-compose.yml
├── Dockerfile
├── start.sh
└── .dockerignore
```

### 6. Comandos Útiles

**Ver el estado del contenedor:**
```bash
docker ps
```

**Ver logs en tiempo real:**
```bash
docker logs -f app-asistencia
```

**Reiniciar el contenedor:**
```bash
docker restart app-asistencia
```

**Entrar al contenedor para debugging:**
```bash
docker exec -it app-asistencia /bin/bash
```

---

## 📊 Endpoints Disponibles

Una vez desplegado, estos serán tus endpoints:

| Endpoint | URL Completa |
|----------|--------------|
| Frontend | https://electo-asistencia.fxtfoe.easypanel.host/ |
| API Docs | https://electo-asistencia.fxtfoe.easypanel.host/docs |
| Health | https://electo-asistencia.fxtfoe.easypanel.host/health |
| Proyectos | https://electo-asistencia.fxtfoe.easypanel.host/api/projects |
| Personas | https://electo-asistencia.fxtfoe.easypanel.host/api/persons |
| Eventos | https://electo-asistencia.fxtfoe.easypanel.host/api/events |

---

## ✅ Checklist de Despliegue

- [ ] Código subido al repositorio Git
- [ ] Easypanel conectado al repositorio
- [ ] Puerto 8000 configurado
- [ ] Dominio configurado correctamente
- [ ] Volume para datos persistentes configurado
- [ ] Build exitoso (revisar logs)
- [ ] Contenedor corriendo (no se cierra)
- [ ] Health check responde OK
- [ ] Frontend carga correctamente
- [ ] API responde en /docs
