# Prácticas · Frontend Svelte

Frontend Svelte 5 y Vite para el sistema de gestión de prácticas profesionales de la carpeta raíz. El API es FastAPI con PostgreSQL (Neon); roles y permisos se consultan desde `/roles/` y `/roles/{rol_id}/modulos`.

## Desarrollo local

1. Inicia la API en la raíz del repositorio: `uvicorn main:app --reload`.
2. En `frontend/`, instala dependencias con `npm install`.
3. Copia `.env.example` a `.env.local` y deja `VITE_API_URL=http://localhost:8000`.
4. Ejecuta `npm run dev` y abre `http://localhost:5173`.

## Compilar

Desde `frontend/`: `npm run build`. Vite genera el sitio estático en `dist/`.

## Despliegue

El frontend Svelte/Vite y la API FastAPI están desplegados como proyectos separados de Vercel. La variable `VITE_API_URL` del frontend apunta al dominio HTTPS de la API. El backend permite solicitudes de la web publicada mediante `FRONTEND_URL`.

Para producción, cargar `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT` y `JWT_SECRET` como variables cifradas del servicio backend. `JWT_SECRET` debe tener al menos 32 caracteres. No subir `.env` ni copiar variables `DB_*` al servicio frontend.

## Roles y límites actuales de la API

Las cuentas se almacenan en `usuarios_sistema`, con contraseñas PBKDF2 y un rol asociado. Un administrador crea las otras cuentas desde Seguridad. La API verifica el token de sesión y consulta `roles_modulos` en cada operación CRUD. La migración de usuarios se crea de forma idempotente al iniciar FastAPI.
