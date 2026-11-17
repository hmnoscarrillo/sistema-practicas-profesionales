"""Create one demo login for each active role missing an account.

Passwords are random and saved to the ignored .demo-accounts.txt file.
Run from the repository root with the configured PostgreSQL database.
"""
from pathlib import Path
import secrets
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.core.auth import _password_hash
from app.core.database import Database


OUTPUT = ROOT / ".demo-accounts.txt"


def main() -> None:
    conn = Database().get_connection()
    if conn is None:
        raise SystemExit("No se pudo conectar a la base configurada.")
    created = []
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT rol_id, nombre FROM roles WHERE estado='Activo' ORDER BY rol_id")
            for role in cursor.fetchall():
                cursor.execute("SELECT 1 FROM usuarios_sistema WHERE rol_id=%s AND estado='Activo' LIMIT 1", (role["rol_id"],))
                if cursor.fetchone():
                    continue
                nombres = f"Demo {role['nombre']}"
                apellidos = "Prácticas"
                password = secrets.token_urlsafe(18)
                cursor.execute("""
                    INSERT INTO usuarios_sistema (nombres, apellidos, password_hash, rol_id)
                    VALUES (%s, %s, %s, %s)
                    RETURNING usuario_id
                """, (nombres, apellidos, _password_hash(password), role["rol_id"]))
                created.append((role["nombre"], nombres, apellidos, password))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    if created:
        with OUTPUT.open("a", encoding="utf-8") as file:
            for role, nombres, apellidos, password in created:
                file.write(f"Rol: {role}\nNombre: {nombres}\nApellido: {apellidos}\nContraseña: {password}\n\n")
    print(f"Cuentas nuevas: {len(created)}")
    print(f"Credenciales guardadas en: {OUTPUT}")
    print("El archivo está excluido de Git; consérvalo en privado.")


if __name__ == "__main__":
    main()
