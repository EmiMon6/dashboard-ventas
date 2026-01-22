# Dashboard de Ventas - Despliegue en EasyPanel

## Pasos para desplegar

### 1. Subir código a GitHub

Primero, crea un repositorio en GitHub y sube el código:

```bash
cd dashboard-ventas
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/TU_USUARIO/dashboard-ventas.git
git push -u origin main
```

### 2. Crear App en EasyPanel

1. Ve a tu panel de EasyPanel
2. Click en **"+ Create"** → **"App"**
3. Selecciona **"Docker Compose"** o **"Dockerfile"**
4. Conecta tu repositorio de GitHub
5. EasyPanel detectará el `Dockerfile` automáticamente

### 3. Configurar Puertos

En la configuración de la app:
- Puerto 8501 → Dashboard (Streamlit)
- Puerto 8502 → API (FastAPI)

Asigna dominios:
- `dashboard-ventas.tu-dominio.com:8501` → Dashboard
- `api-ventas.tu-dominio.com:8502` → API

### 4. Variables de Entorno (opcional)

No se requieren variables de entorno por defecto.

### 5. Volumen para Datos

Crea un volumen persistente en EasyPanel:
- Mount path: `/app/data`
- Esto asegura que el CSV no se pierda al reiniciar

### 6. Deploy

Click en **"Deploy"** y espera a que el build termine.

## URLs finales

Después del deploy tendrás:
- Dashboard: `https://dashboard-ventas.yny2jy.easypanel.host`
- API: `https://api-ventas.yny2jy.easypanel.host`

## Actualizar datos desde n8n

```
POST https://api-ventas.yny2jy.easypanel.host/api/upload-data
GET  https://api-ventas.yny2jy.easypanel.host/api/reminders
```
