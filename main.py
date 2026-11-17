from contextlib import asynccontextmanager
import logging
import os
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
    rutas_roles,
    rutas_seguimientos,
    rutas_tutor_academicos,
    rutas_tutor_empresarials,
)
from app.core.auth import authorize_request, ensure_user_table
from app.core.database import Database, ensure_database_indexes, ensure_soft_delete_columns
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


@app.middleware("http")
async def autenticar_y_autorizar(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)
    try:
        request.state.user = authorize_request(request)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)
    return await call_next(request)


# CORS must wrap authentication too, so browser clients can read 401/403 responses.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"] + ([os.getenv("FRONTEND_URL")] if os.getenv("FRONTEND_URL") else []),
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
