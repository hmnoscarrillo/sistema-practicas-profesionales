from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
import os
from pathlib import Path
import threading
from typing import Optional

from dotenv import load_dotenv
from fastapi import HTTPException
import psycopg2
from psycopg2 import extensions, pool
from psycopg2.errors import CheckViolation, DataError, ForeignKeyViolation, UniqueViolation
from psycopg2.extras import RealDictCursor, RealDictRow

BASE_DIR = Path(__file__).resolve().parents[2]

# Carga .env.local para desarrollo si existe; en caso contrario conserva el .env de despliegue.
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / ".env.local", override=True)

_POOLS: dict[tuple, pool.ThreadedConnectionPool] = {}
_POOL_LOCK = threading.Lock()


class _PooledConnection:
    """Envoltorio que devuelve la conexión al pool al llamar close()."""

    def __init__(self, conn_pool: pool.ThreadedConnectionPool, raw_conn):
        self._pool = conn_pool
        self._conn = raw_conn
        self._returned = False

    def __getattr__(self, name):
        return getattr(self._conn, name)

    def __enter__(self):
        return self._conn.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._conn.__exit__(exc_type, exc_val, exc_tb)

    def close(self):
        if self._returned:
            return
        self._returned = True
        discard = bool(self._conn.closed)
        if not discard:
            try:
                if self._conn.info.transaction_status != extensions.TRANSACTION_STATUS_IDLE:
                    self._conn.rollback()
            except Exception:
                discard = True
        try:
            self._pool.putconn(self._conn, close=discard)
        except Exception:
            if not self._conn.closed:
                self._conn.close()


class Database:
    def __init__(self):
        self.dsn = os.getenv("DATABASE_URL")
        self.host = os.getenv("DB_HOST")
        self.database = os.getenv("DB_NAME")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.port = os.getenv("DB_PORT", "5432")

    def _connect_kwargs(self) -> tuple[tuple, dict]:
        options: dict = {
            "cursor_factory": RealDictCursor,
            "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "5")),
        }
        if self.dsn:
            # La conexión local normalmente no usa SSL; Neon requiere SSL.
            sslmode = os.getenv("DB_SSLMODE", "require" if "neon.tech" in self.dsn else "prefer")
            options["sslmode"] = sslmode
            key = ("dsn", self.dsn, sslmode)
            return key, {"dsn": self.dsn, **options}

        if not all((self.host, self.database, self.user, self.password)):
            raise RuntimeError("Configura DATABASE_URL o DB_HOST, DB_NAME, DB_USER y DB_PASSWORD.")

        sslmode = os.getenv("DB_SSLMODE", "require" if "neon.tech" in (self.host or "") else "prefer")
        options.update(
            host=self.host,
            dbname=self.database,
            user=self.user,
            password=self.password,
            port=self.port,
            sslmode=sslmode,
        )
        key = ("params", self.host, self.database, self.user, self.port, sslmode)
        return key, options

    def _get_pool(self) -> Optional[pool.ThreadedConnectionPool]:
        key, kwargs = self._connect_kwargs()
        with _POOL_LOCK:
            existing = _POOLS.get(key)
            if existing is not None and not existing.closed:
                return existing
            created = pool.ThreadedConnectionPool(minconn=1, maxconn=10, **kwargs)
            _POOLS[key] = created
            return created

    def get_connection(self):
        try:
            conn_pool = self._get_pool()
            if conn_pool is None:
                return None
            raw_conn = conn_pool.getconn()
            if raw_conn.closed:
                conn_pool.putconn(raw_conn, close=True)
                raw_conn = conn_pool.getconn()
            return _PooledConnection(conn_pool, raw_conn)
        except Exception as e:
            print(f"Error de conexión a la BD: {e}")
            return None

    @contextmanager
    def connection(self, commit: bool = False):
        conn = self.get_connection()
        if conn is None:
            raise HTTPException(status_code=503, detail="Base de datos no disponible.")
        try:
            yield conn
            if commit:
                conn.commit()
        except HTTPException:
            if not conn.closed:
                conn.rollback()
            raise
        except UniqueViolation:
            if not conn.closed:
                conn.rollback()
            raise
        except ForeignKeyViolation as exc:
            if not conn.closed:
                conn.rollback()
            raise HTTPException(
                status_code=422,
                detail="Uno de los registros relacionados seleccionados no existe o no está activo.",
            ) from exc
        except (CheckViolation, DataError) as exc:
            if not conn.closed:
                conn.rollback()
            raise HTTPException(
                status_code=422,
                detail="Los datos enviados no cumplen el formato o rango requerido.",
            ) from exc
        except Exception:
            if not conn.closed:
                conn.rollback()
            raise
        finally:
            conn.close()

    @contextmanager
    def cursor(self, commit: bool = False):
        with self.connection(commit=commit) as conn:
            with conn.cursor() as cur:
                yield cur

    def ping(self) -> bool:
        try:
            with self.cursor() as cur:
                cur.execute("SELECT 1")
                return cur.fetchone() is not None
        except Exception:
            return False


def ensure_soft_delete_columns() -> None:
    """Agrega metadatos de baja lógica a tablas heredadas que aún no los tengan."""
    conn = Database().get_connection()
    if conn is None:
        raise RuntimeError("No se pudo conectar a PostgreSQL para revisar columnas de estado.")
    specs = {
        "programas": ("Inactivo", "estado VARCHAR(30) NOT NULL DEFAULT 'Activo'"),
        "estudiantes": ("Inactivo", "estado VARCHAR(30) NOT NULL DEFAULT 'Activo'"),
        "empresas": ("Inactiva", "estado VARCHAR(30) NOT NULL DEFAULT 'Activa'"),
        "convenios": ("Inactivo", "estado VARCHAR(30) NOT NULL DEFAULT 'Vigente'"),
        "practicas": ("Inactiva", "estado VARCHAR(30) NOT NULL DEFAULT 'En proceso'"),
        "documentos": ("Inactivo", "estado VARCHAR(30) NOT NULL DEFAULT 'Pendiente'"),
        "seguimientos": ("Inactivo", "estado VARCHAR(30) NOT NULL DEFAULT 'Pendiente'"),
        "evaluaciones": ("Inactivo", "estado VARCHAR(30) NOT NULL DEFAULT 'Activo'"),
        "personas": ("Inactivo", "estado VARCHAR(30) NOT NULL DEFAULT 'Activo'"),
        "tutores_academicos": ("Inactivo", "estado VARCHAR(30) NOT NULL DEFAULT 'Activo'"),
        "tutores_empresariales": ("Inactivo", "estado VARCHAR(30) NOT NULL DEFAULT 'Activo'"),
    }
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT to_regclass('public.usuarios_sistema') AS table_name")
            if cursor.fetchone()["table_name"]:
                cursor.execute("SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='usuarios_sistema' AND column_name='estado'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE public.usuarios_sistema ADD COLUMN estado VARCHAR(30) NOT NULL DEFAULT 'Activo'")
                cursor.execute("SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='usuarios_sistema' AND column_name='actualizado'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE public.usuarios_sistema ADD COLUMN actualizado TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP")
            for table, (_inactive, definition) in specs.items():
                cursor.execute("SELECT to_regclass(%s) AS table_name", (f"public.{table}",))
                if not cursor.fetchone()["table_name"]:
                    continue
                cursor.execute("SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name=%s AND column_name='estado'", (table,))
                if not cursor.fetchone():
                    cursor.execute(f"ALTER TABLE public.{table} ADD COLUMN {definition}")
                cursor.execute("SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name=%s AND column_name='actualizado'", (table,))
                if not cursor.fetchone():
                    cursor.execute(f"ALTER TABLE public.{table} ADD COLUMN actualizado TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def ensure_database_indexes() -> None:
    """Crea índices idempotentes sobre claves foráneas y columnas frecuentes de filtro."""
    conn = Database().get_connection()
    if conn is None:
        raise RuntimeError("No se pudo conectar a PostgreSQL para verificar índices.")
    index_specs = [
        ("estudiantes", "ix_estudiantes_programa_id", "programa_id"),
        ("estudiantes", "ix_estudiantes_estado", "estado"),
        ("empresas", "ix_empresas_estado", "estado"),
        ("programas", "ix_programas_estado", "estado"),
        ("convenios", "ix_convenios_empresa_id", "empresa_id"),
        ("convenios", "ix_convenios_programa_id", "programa_id"),
        ("convenios", "ix_convenios_estado", "estado"),
        ("practicas", "ix_practicas_estudiante_id", "estudiante_id"),
        ("practicas", "ix_practicas_empresa_id", "empresa_id"),
        ("practicas", "ix_practicas_programa_id", "programa_id"),
        ("practicas", "ix_practicas_convenio_id", "convenio_id"),
        ("practicas", "ix_practicas_tutor_academico_id", "tutor_academico_id"),
        ("practicas", "ix_practicas_tutor_empresarial_id", "tutor_empresarial_id"),
        ("practicas", "ix_practicas_estado", "estado"),
        ("seguimientos", "ix_seguimientos_practica_id", "practica_id"),
        ("seguimientos", "ix_seguimientos_tutor_academico_id", "tutor_academico_id"),
        ("seguimientos", "ix_seguimientos_estado", "estado"),
        ("evaluaciones", "ix_evaluaciones_practica_id", "practica_id"),
        ("evaluaciones", "ix_evaluaciones_estado", "estado"),
        ("documentos", "ix_documentos_practica_id", "practica_id"),
        ("documentos", "ix_documentos_estado", "estado"),
        ("usuarios_sistema", "ix_usuarios_sistema_rol_id", "rol_id"),
        ("usuarios_sistema", "ix_usuarios_sistema_estado", "estado"),
    ]
    try:
        with conn.cursor() as cursor:
            existing_tables: dict[str, bool] = {}
            for table, index_name, column in index_specs:
                if table not in existing_tables:
                    cursor.execute("SELECT to_regclass(%s) AS table_name", (f"public.{table}",))
                    existing_tables[table] = cursor.fetchone()["table_name"] is not None
                if not existing_tables[table]:
                    continue
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON public.{table} ({column})")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def serializar_dato(valor):
    """Convierte los tipos de PostgreSQL a valores JSON nativos."""
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, RealDictRow):
        return {clave: serializar_dato(dato) for clave, dato in valor.items()}
    if isinstance(valor, dict):
        return {clave: serializar_dato(dato) for clave, dato in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [serializar_dato(dato) for dato in valor]
    return valor
