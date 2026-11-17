from contextlib import asynccontextmanager
import logging
import os
import re
import threading

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from psycopg2.errors import UniqueViolation

from app.api import (
    rutas_auth,
    rutas_convenios,
    rutas_documentos,
    rutas_empresas,
    rutas_estudiantes,
    rutas_evaluacions,
    rutas_personas,
    rutas_practicas,
    rutas_programas,
    rutas_reportes,
    rutas_roles,
    rutas_seguimientos,
    rutas_tablero,
    rutas_tutor_academicos,
    rutas_tutor_empresarials,
)
from app.core.auth import authorize_request, decode_token, ensure_user_table
from app.core.database import Database, ensure_database_indexes, ensure_soft_delete_columns, serializar_dato
from app.core.people_schema import ensure_people_schema

logger = logging.getLogger("practicas.api")
_esquema_inicializado = False
_esquema_lock = threading.Lock()


def _asegurar_esquema_una_vez() -> None:
    global _esquema_inicializado
    if _esquema_inicializado:
        return
    with _esquema_lock:
        if _esquema_inicializado:
            return
        try:
            ensure_user_table()
            ensure_people_schema()
            ensure_soft_delete_columns()
            ensure_database_indexes()
            _esquema_inicializado = True
        except Exception as exc:
            logger.warning("No se pudo completar la verificación inicial de PostgreSQL: %s", exc)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _asegurar_esquema_una_vez()
    yield


app = FastAPI(
    title="API Sistema de Gestión de Prácticas Profesionales",
    description="Backend modular con FastAPI y PostgreSQL (Neon) para Sistema de Gestión de Prácticas Profesionales",
    version="1.0.0",
    lifespan=lifespan,
)


def generar_openapi_con_autenticacion():
    """Describe a Swagger qué rutas requieren un token Bearer."""
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema.setdefault("components", {}).setdefault("securitySchemes", {})["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Inicia sesión en POST /auth/login y pega aquí el access_token recibido.",
    }

    rutas_publicas = {
        ("/", "get"),
        ("/health", "get"),
        ("/auth/login", "post"),
        ("/auth/bootstrap", "post"),
    }
    metodos_http = {"get", "post", "put", "patch", "delete", "options", "head"}
    for ruta, operaciones in schema.get("paths", {}).items():
        for metodo, operacion in operaciones.items():
            if metodo in metodos_http and (ruta, metodo) not in rutas_publicas:
                operacion["security"] = [{"BearerAuth": []}]

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = generar_openapi_con_autenticacion


@app.exception_handler(UniqueViolation)
async def manejar_duplicado(_request: Request, _exc: UniqueViolation):
    return JSONResponse(status_code=409, content={"detail": "Ya existe un registro con esos datos únicos."})


def _autorizar_ruta_analitica(request: Request) -> dict:
    auth_header = request.headers.get("authorization", "")
    match = re.fullmatch(r"Bearer\s+(.+)", auth_header, flags=re.IGNORECASE)
    user_id = decode_token(match.group(1)) if match else None
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Inicia sesión para continuar.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    with Database().cursor() as cursor:
        cursor.execute(
            """
            SELECT u.usuario_id, u.nombres, u.apellidos, u.rol_id, r.nombre AS rol_nombre
            FROM usuarios_sistema u
            JOIN roles r ON r.rol_id = u.rol_id
            WHERE u.usuario_id = %s AND u.estado = 'Activo' AND r.estado = 'Activo'
            """,
            (user_id,),
        )
        user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="La cuenta está inactiva o ya no existe.")
    return serializar_dato(user)


@app.middleware("http")
async def autenticar_y_autorizar(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)
    path = request.url.path.rstrip("/") or "/"
    try:
        if path == "/tablero" or path.startswith("/tablero/") or path == "/reportes" or path.startswith("/reportes/"):
            request.state.user = _autorizar_ruta_analitica(request)
        else:
            request.state.user = authorize_request(request)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)
    return await call_next(request)


_cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://localhost",
    "http://localhost",
    "capacitor://localhost",
]
if os.getenv("FRONTEND_URL"):
    _cors_origins.append(os.getenv("FRONTEND_URL").strip().rstrip("/"))

# CORS must wrap authentication too, so browser clients can read 401/403 responses.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conectamos cada módulo de rutas a la aplicación principal
app.include_router(rutas_roles.router)
app.include_router(rutas_auth.router)
app.include_router(rutas_personas.router)
app.include_router(rutas_programas.router)
app.include_router(rutas_estudiantes.router)
app.include_router(rutas_empresas.router)

# Rutas de tutores
app.include_router(rutas_tutor_academicos.router)
app.include_router(rutas_tutor_academicos.router_compat)

app.include_router(rutas_tutor_empresarials.router)
app.include_router(rutas_tutor_empresarials.router_compat)

app.include_router(rutas_convenios.router)
app.include_router(rutas_practicas.router)
app.include_router(rutas_seguimientos.router)
app.include_router(rutas_evaluacions.router)
app.include_router(rutas_documentos.router)
app.include_router(rutas_tablero.router)
app.include_router(rutas_reportes.router)


@app.get("/")
def estado_api():
    return {
        "mensaje": "API Para Sistema de Gestión de Prácticas Profesionales",
        "estado": "Activo",
        "framework": "FastAPI + PostgreSQL (Neon)",
    }


@app.get("/health")
def salud():
    _asegurar_esquema_una_vez()
    conectada = Database().ping()
    return {
        "estado": "Activo",
        "base_datos": "Conectada" if conectada else "No disponible",
    }
