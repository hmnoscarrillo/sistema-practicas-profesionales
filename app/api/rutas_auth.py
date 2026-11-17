from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from psycopg2.errors import UniqueViolation

from app.core.auth import _normalize, _password_hash, bootstrap_admin, create_user, login
from app.core.database import Database, serializar_dato

router = APIRouter(prefix="/auth", tags=["Autenticación"])


class LoginRequest(BaseModel):
    nombres: str = Field(description="Nombre registrado en la cuenta.")
    apellidos: str = Field(description="Apellido registrado en la cuenta.")
    password: str = Field(description="Contraseña de la cuenta.")


@router.post(
    "/login",
    summary="Iniciar sesión",
    description="Indica nombre, apellido y contraseña. La respuesta incluye el access_token que se usa en Authorize.",
)
def iniciar_sesion(body: LoginRequest):
    return login(body.model_dump())


@router.post("/bootstrap", status_code=201)
def inicializar_administrador(body: dict):
    return bootstrap_admin(body)


@router.get("/me")
def usuario_actual(request: Request):
    return request.state.user


@router.get("/bootstrap-status")
def estado_inicializacion():
    conn = Database().get_connection()
    if conn is None:
        raise HTTPException(status_code=503, detail="Base de datos no disponible.")
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT to_regclass('public.usuarios_sistema') IS NOT NULL AS tabla_existe")
            exists = cursor.fetchone()["tabla_existe"]
            if not exists:
                return {"initialized": False}
            cursor.execute("SELECT EXISTS (SELECT 1 FROM usuarios_sistema) AS initialized")
            return cursor.fetchone()
    finally:
        conn.close()


@router.get("/users")
def listar_usuarios():
    conn = Database().get_connection()
    if conn is None:
        raise HTTPException(status_code=503, detail="Base de datos no disponible.")
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.usuario_id, u.nombres, u.apellidos, u.rol_id, r.nombre AS rol_nombre,
                       u.estado, u.creado
                FROM usuarios_sistema u JOIN roles r ON r.rol_id = u.rol_id
                ORDER BY u.usuario_id
            """)
            return serializar_dato(cursor.fetchall())
    finally:
        conn.close()


@router.post("/users", status_code=201)
def crear_usuario(body: dict, request: Request):
    return create_user(body, request.state.user)


@router.put("/users/{usuario_id}")
def actualizar_usuario(usuario_id: int, body: dict, request: Request):
    nombres = _normalize(str(body.get("nombres", "")))
    apellidos = _normalize(str(body.get("apellidos", "")))
    password = str(body.get("password", ""))
    try:
        rol_id = int(body.get("rol_id"))
    except (ValueError, TypeError):
        rol_id = 0
    if not nombres or not apellidos or not rol_id:
        raise HTTPException(status_code=422, detail="Indica nombre, apellido y un rol.")
    if password and len(password) < 12:
        raise HTTPException(status_code=422, detail="La contraseña debe tener al menos 12 caracteres.")
    conn = Database().get_connection()
    if conn is None:
        raise HTTPException(status_code=503, detail="Base de datos no disponible.")
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM roles WHERE rol_id = %s AND estado = 'Activo'", (rol_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=422, detail="El rol seleccionado no está activo.")
            cursor.execute("SELECT u.rol_id, r.nombre AS rol_nombre FROM usuarios_sistema u JOIN roles r ON r.rol_id=u.rol_id WHERE u.usuario_id=%s AND u.estado='Activo'", (usuario_id,))
            existing = cursor.fetchone()
            if not existing:
                raise HTTPException(status_code=404, detail="No se encontró la cuenta.")
            if existing["rol_nombre"].casefold() == "administrador" and rol_id != existing["rol_id"]:
                cursor.execute("SELECT COUNT(*) AS cantidad FROM usuarios_sistema u JOIN roles r ON r.rol_id=u.rol_id WHERE u.estado='Activo' AND r.estado='Activo' AND lower(r.nombre)='administrador'")
                if cursor.fetchone()["cantidad"] <= 1:
                    raise HTTPException(status_code=409, detail="Debe permanecer al menos una cuenta administradora activa.")
            if password:
                cursor.execute("UPDATE usuarios_sistema SET nombres=%s, apellidos=%s, rol_id=%s, password_hash=%s, actualizado=CURRENT_TIMESTAMP WHERE usuario_id=%s RETURNING usuario_id, nombres, apellidos, rol_id, estado, creado", (nombres, apellidos, rol_id, _password_hash(password), usuario_id))
            else:
                cursor.execute("UPDATE usuarios_sistema SET nombres=%s, apellidos=%s, rol_id=%s, actualizado=CURRENT_TIMESTAMP WHERE usuario_id=%s RETURNING usuario_id, nombres, apellidos, rol_id, estado, creado", (nombres, apellidos, rol_id, usuario_id))
            result = serializar_dato(cursor.fetchone())
        conn.commit()
        return result
    except UniqueViolation as error:
        conn.rollback()
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese nombre y apellido.") from error
    except HTTPException:
        conn.rollback()
        raise
    finally:
        conn.close()


@router.delete("/users/{usuario_id}", status_code=204)
def eliminar_usuario(usuario_id: int, request: Request):
    if usuario_id == request.state.user.get("usuario_id"):
        raise HTTPException(status_code=409, detail="No puedes eliminar la cuenta con la que tienes la sesión activa.")
    conn = Database().get_connection()
    if conn is None:
        raise HTTPException(status_code=503, detail="Base de datos no disponible.")
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT u.usuario_id, r.nombre AS rol_nombre FROM usuarios_sistema u JOIN roles r ON r.rol_id=u.rol_id WHERE u.usuario_id=%s AND u.estado='Activo'", (usuario_id,))
            existing = cursor.fetchone()
            if not existing:
                raise HTTPException(status_code=404, detail="No se encontró la cuenta.")
            if existing["rol_nombre"].casefold() == "administrador":
                cursor.execute("SELECT COUNT(*) AS cantidad FROM usuarios_sistema u JOIN roles r ON r.rol_id=u.rol_id WHERE u.estado='Activo' AND r.estado='Activo' AND lower(r.nombre)='administrador'")
                if cursor.fetchone()["cantidad"] <= 1:
                    raise HTTPException(status_code=409, detail="Debe permanecer al menos una cuenta administradora activa.")
            cursor.execute("UPDATE usuarios_sistema SET estado='Inactivo', actualizado=CURRENT_TIMESTAMP WHERE usuario_id=%s", (usuario_id,))
        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    finally:
        conn.close()

