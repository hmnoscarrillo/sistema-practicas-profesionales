# Sistema de gestión de prácticas profesionales

Aplicación web con frontend Svelte 5, API FastAPI y PostgreSQL en Neon. La API consulta la base de datos para los módulos y permisos de cada rol.

## Sitio público

- Frontend: https://sistema-practicas-web.vercel.app
- API: https://sistema-practicas-profesionales.vercel.app

## Desarrollo local

En este computador el backend local está escuchando en `http://localhost:8000` y el frontend en `http://localhost:5173`. Para iniciarlos después de reiniciar Windows, ejecuta `uvicorn main:app --reload` desde la raíz y `npm run dev` desde `frontend/`. La configuración del frontend local apunta a la API local.

## Acceso y permisos

El Administrador inicial se creó en la base conectada. El nombre, apellido y contraseña inicial se entregaron al responsable del proyecto por separado. Desde Seguridad, el Administrador puede crear las cuentas restantes y asignarles uno de los roles activos.

Cada cuenta tiene un rol guardado en `usuarios_sistema`. El backend firma sesiones, guarda contraseñas con PBKDF2 y verifica en cada solicitud los permisos de `roles_modulos`. Los identificadores de cuenta y de las relaciones se usan internamente; no aparecen como campos de usuario.

## Base de datos local

En este equipo PostgreSQL 18.6 está instalado como servicio local en el puerto `5433`, y la base `practicas` contiene una copia de Neon. `.env.local` configura la API para esa base y tiene prioridad sobre `.env`; Neon sigue configurado en `.env`. El servicio local se inicia con Windows. Si necesitas volver a sincronizar la copia, usa `pg_dump` y `pg_restore` de PostgreSQL 18.

## Cuentas para demostrar los roles

`scripts/crear_cuentas_demo.py` crea una cuenta aleatoria para cada rol activo que todavía no tenga una. Las credenciales se guardan en `.demo-accounts.txt`, archivo local excluido de Git. Ejecútalo una sola vez desde la raíz con `myvenv\Scripts\python.exe scripts\crear_cuentas_demo.py`. Los permisos de cada cuenta vienen de `roles_modulos`.

## Borrado lógico y tablas

Las acciones de eliminar cambian el estado del registro a inactivo y lo excluyen de los listados normales; conservan la fila y el historial relacionado. El componente compartido de tablas inicializa DataTables, mientras mantiene los filtros y la paginación de la interfaz.

## Despliegue

Frontend y API están desplegados en dos proyectos separados de Vercel. Las variables de conexión y firma se guardan como valores sensibles solo en el proyecto de la API; el frontend apunta a la URL HTTPS pública de la API.
