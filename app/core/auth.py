import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time
import unicodedata
from typing import Optional

from fastapi import HTTPException, Request
from psycopg2.errors import UniqueViolation

from app.core.database import Database, serializar_dato

TOKEN_TTL_SECONDS = 8 * 60 * 60
PBKDF2_ROUNDS = 310_000


def _normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).strip().split())


def _password_hash(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS)
    return f"pbkdf2_sha256${PBKDF2_ROUNDS}${_b64(salt)}${_b64(digest)}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        scheme, rounds, salt, expected = stored.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), _unb64(salt), int(rounds))
        return hmac.compare_digest(actual, _unb64(expected))
    except (ValueError, TypeError):
        return False


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def issue_token(user: dict) -> str:
    secret = os.getenv("JWT_SECRET")
    if not secret or len(secret) < 32:
        raise RuntimeError("JWT_SECRET debe configurarse con al menos 32 caracteres.")
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _b64(json.dumps({"sub": user["usuario_id"], "iat": int(time.time()), "exp": int(time.time()) + TOKEN_TTL_SECONDS}, separators=(",", ":")).encode())
    signing_input = f"{header}.{payload}"
    signature = hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64(signature)}"


def decode_token(token: str) -> Optional[int]:
    try:
        header, payload, signature = token.split(".", 2)
        secret = os.getenv("JWT_SECRET", "")
        if len(secret) < 32:
            return None
        expected = hmac.new(secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _unb64(signature)):
            return None
        claims = json.loads(_unb64(payload))
        if int(claims["exp"]) <= int(time.time()):
            return None
        return int(claims["sub"])
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return None


def ensure_user_table() -> None:
    conn = Database().get_connection()
    if conn is None:
        raise RuntimeError("No se pudo conectar a PostgreSQL para inicializar las cuentas.")
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios_sistema (
                    usuario_id BIGSERIAL PRIMARY KEY,
                    nombres VARCHAR(120) NOT NULL,
                    apellidos VARCHAR(120) NOT NULL,
                    password_hash TEXT NOT NULL,
                    rol_id INTEGER NOT NULL REFERENCES roles(rol_id),
                    estado VARCHAR(20) NOT NULL DEFAULT 'Activo',
                    creado TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    CONSTRAINT uq_usuarios_sistema_nombre UNIQUE (nombres, apellidos)
                );
                CREATE UNIQUE INDEX IF NOT EXISTS uq_usuarios_sistema_nombre_ci
                    ON usuarios_sistema (lower(nombres), lower(apellidos));
            """)
        conn.commit()
    finally:
        conn.close()


def bootstrap_admin(body: dict) -> dict:
    configured = os.getenv("BOOTSTRAP_SECRET", "")
    supplied = str(body.get("bootstrap_secret", ""))
    if not configured or not hmac.compare_digest(configured, supplied):
        raise HTTPException(status_code=403, detail="Inicialización no autorizada.")
    nombres = _normalize(str(body.get("nombres", "")))
    apellidos = _normalize(str(body.get("apellidos", "")))
    password = str(body.get("password", ""))
    if not nombres or not apellidos or len(password) < 12:
        raise HTTPException(status_code=422, detail="Indica nombre, apellido y una contraseña de al menos 12 caracteres.")

    conn = Database().get_connection()
    if conn is None:
        raise HTTPException(status_code=503, detail="Base de datos no disponible.")
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(91827, 4106)")
            cursor.execute("SELECT COUNT(*) AS cantidad FROM usuarios_sistema")
            if cursor.fetchone()["cantidad"]:
                raise HTTPException(status_code=409, detail="La inicialización ya fue completada.")
            cursor.execute("SELECT rol_id FROM roles WHERE nombre = 'Administrador' AND estado = 'Activo' LIMIT 1")
            role = cursor.fetchone()
            if not role:
                raise HTTPException(status_code=500, detail="No existe un rol Administrador activo.")
            cursor.execute("""
                INSERT INTO usuarios_sistema (nombres, apellidos, password_hash, rol_id)
                VALUES (%s, %s, %s, %s) RETURNING usuario_id, nombres, apellidos, rol_id
            """, (nombres, apellidos, _password_hash(password), role["rol_id"]))
            user = serializar_dato(cursor.fetchone())
        conn.commit()
        return user
    except HTTPException:
        conn.rollback()
        raise
    except UniqueViolation as error:
        conn.rollback()
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese nombre y apellido.") from error
    finally:
        conn.close()


def login(body: dict) -> dict:
    nombres = _normalize(str(body.get("nombres", "")))
    apellidos = _normalize(str(body.get("apellidos", "")))
    password = str(body.get("password", ""))
    if not nombres or not apellidos or not password:
        raise HTTPException(status_code=422, detail="Completa nombre, apellido y contraseña.")
    conn = Database().get_connection()
    if conn is None:
        raise HTTPException(status_code=503, detail="Base de datos no disponible.")
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.usuario_id, u.nombres, u.apellidos, u.password_hash, u.rol_id, r.nombre AS rol_nombre
                FROM usuarios_sistema u JOIN roles r ON r.rol_id = u.rol_id
                WHERE lower(u.nombres) = lower(%s) AND lower(u.apellidos) = lower(%s)
                  AND u.estado = 'Activo' AND r.estado = 'Activo'
            """, (nombres, apellidos))
            user = cursor.fetchone()
    finally:
        conn.close()
    if not user or not _verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Nombre, apellido o contraseña incorrectos.")
    public_user = {key: user[key] for key in ("usuario_id", "nombres", "apellidos", "rol_id", "rol_nombre")}
    public_user["access_token"] = issue_token(user)
    public_user["token_type"] = "bearer"
    public_user["expires_in"] = TOKEN_TTL_SECONDS
    return serializar_dato(public_user)


def create_user(body: dict, actor: dict) -> dict:
    nombres = _normalize(str(body.get("nombres", "")))
    apellidos = _normalize(str(body.get("apellidos", "")))
    password = str(body.get("password", ""))
    try:
        rol_id = int(body.get("rol_id"))
    except (ValueError, TypeError):
        rol_id = 0
    if not nombres or not apellidos or len(password) < 12 or not rol_id:
        raise HTTPException(status_code=422, detail="Indica nombre, apellido, un rol y una contraseña de al menos 12 caracteres.")
    conn = Database().get_connection()
    if conn is None:
        raise HTTPException(status_code=503, detail="Base de datos no disponible.")
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM roles WHERE rol_id = %s AND estado = 'Activo'", (rol_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=422, detail="El rol seleccionado no está activo.")
            cursor.execute("""
                INSERT INTO usuarios_sistema (nombres, apellidos, password_hash, rol_id)
                VALUES (%s, %s, %s, %s)
                RETURNING usuario_id, nombres, apellidos, rol_id, estado, creado
            """, (nombres, apellidos, _password_hash(password), rol_id))
            user = serializar_dato(cursor.fetchone())
        conn.commit()
        return user
    except UniqueViolation as error:
        conn.rollback()
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese nombre y apellido.") from error
    except HTTPException:
        conn.rollback()
        raise
    finally:
        conn.close()


def seed_role_accounts() -> list[dict]:
    """Ensure each active role has one password-protected demo account."""
    conn = Database().get_connection()
    if conn is None:
        raise RuntimeError("No se pudo conectar a PostgreSQL para preparar cuentas de demostración.")
    accounts = []
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(91827, 4107)")
            cursor.execute("SELECT rol_id, nombre FROM roles WHERE estado='Activo' ORDER BY rol_id")
            for role in cursor.fetchall():
                base = {
                    "Administrador": ("Cuenta", "Administradora"),
                    "Coordinador": ("Cuenta", "Coordinadora"),
                    "Profesor": ("Cuenta", "Docente"),
                    "Estudiante": ("Cuenta", "Estudiante"),
                }.get(role["nombre"], ("Usuario", role["nombre"]))
                first, last = base
                # Use a unique, non-secret display name if a real account already owns the generic name.
                cursor.execute("SELECT 1 FROM usuarios_sistema WHERE lower(nombres)=lower(%s) AND lower(apellidos)=lower(%s)", (first, last))
                if cursor.fetchone():
                    first, last = (f"Demo {role['nombre']}", "Prácticas")
                cursor.execute("""
                    INSERT INTO usuarios_sistema (nombres, apellidos, password_hash, rol_id)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    RETURNING usuario_id, nombres, apellidos, rol_id
                """, (first, last, _password_hash(secrets.token_urlsafe(24)), role["rol_id"]))
                created = cursor.fetchone()
                if created:
                    accounts.append({"usuario_id": created["usuario_id"], "rol": role["nombre"], "nombres": created["nombres"], "apellidos": created["apellidos"]})
            conn.commit()
        return accounts
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


RESOURCE_CODES = {
    "programas": "PROGRAMAS", "estudiantes": "ESTUDIANTES", "empresas": "EMPRESAS",
    "tutores-academicos": "TUTORES_ACADEMICOS", "tutores_academicos": "TUTORES_ACADEMICOS",
    "tutores-empresariales": "TUTORES_EMPRESARIALES", "tutores_empresariales": "TUTORES_EMPRESARIALES",
    "convenios": "CONVENIOS", "personas": "PERSONAS", "practicas": "PRACTICAS", "seguimientos": "SEGUIMIENTOS",
    "evaluaciones": "EVALUACIONES", "documentos": "DOCUMENTOS", "roles": "SEGURIDAD",
}
ACTION_COLUMNS = {"GET": "puede_leer", "POST": "puede_crear", "PUT": "puede_actualizar", "PATCH": "puede_actualizar", "DELETE": "puede_eliminar"}


def _public_route(request: Request) -> bool:
    path = request.url.path.rstrip("/") or "/"
    public_get_routes = {"/", "/health", "/docs", "/openapi.json", "/redoc", "/docs/oauth2-redirect"}
    public_post_routes = {"/auth/login", "/auth/bootstrap"}
    return (request.method == "GET" and path in public_get_routes) or (
        request.method == "POST" and path in public_post_routes
    )


def authorize_request(request: Request) -> Optional[dict]:
    if _public_route(request):
        return None
    auth_header = request.headers.get("authorization", "")
    match = re.fullmatch(r"Bearer\s+(.+)", auth_header, flags=re.IGNORECASE)
    user_id = decode_token(match.group(1)) if match else None
    if not user_id:
        raise HTTPException(status_code=401, detail="Inicia sesión para continuar.", headers={"WWW-Authenticate": "Bearer"})
    conn = Database().get_connection()
    if conn is None:
        raise HTTPException(status_code=503, detail="Base de datos no disponible.")
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.usuario_id, u.nombres, u.apellidos, u.rol_id, r.nombre AS rol_nombre
                FROM usuarios_sistema u JOIN roles r ON r.rol_id = u.rol_id
                WHERE u.usuario_id = %s AND u.estado = 'Activo' AND r.estado = 'Activo'
            """, (user_id,))
            user = cursor.fetchone()
            if not user:
                raise HTTPException(status_code=401, detail="La cuenta está inactiva o ya no existe.")

            parts = request.url.path.strip("/").split("/")
            if parts[0] == "auth" and len(parts) > 1 and parts[1] == "users":
                if user["rol_nombre"].casefold() != "administrador":
                    raise HTTPException(status_code=403, detail="Solo el administrador puede gestionar cuentas.")
                return serializar_dato(user)

            # La sesión necesita consultar su propio perfil antes de cargar permisos.
            if request.method == "GET" and parts == ["auth", "me"]:
                return serializar_dato(user)

            # Cada usuario puede cargar los módulos autorizados de su propio rol.
            # Solo Administración puede consultar permisos de otros roles.
            if request.method == "GET" and len(parts) == 3 and parts[0] == "roles" and parts[2] == "modulos":
                try:
                    requested_role_id = int(parts[1])
                except ValueError:
                    requested_role_id = 0
                if requested_role_id == user["rol_id"] or user["rol_nombre"].casefold() == "administrador":
                    return serializar_dato(user)

            code = RESOURCE_CODES.get(parts[0])
            action_column = ACTION_COLUMNS.get(request.method)
            if not code or not action_column:
                raise HTTPException(status_code=403, detail="Ruta o acción no autorizada.")
            cursor.execute("""
                SELECT rm.puede_crear, rm.puede_leer, rm.puede_actualizar, rm.puede_eliminar
                FROM roles_modulos rm JOIN modulos m ON m.modulo_id = rm.modulo_id
                WHERE rm.rol_id = %s AND m.codigo = %s
                  AND rm.estado = 'Activo' AND m.estado = 'Activo'
            """, (user["rol_id"], code))
            permission = cursor.fetchone()
            if not permission or not permission[action_column]:
                raise HTTPException(status_code=403, detail="Tu rol no tiene permiso para esta acción.")
            return serializar_dato(user)
    finally:
        conn.close()

