from app.core.database import Database, serializar_dato
from app.models.persona import Persona


_SELECT = """
    SELECT p.persona_id, p.documento, p.nombres, p.apellidos, p.correo,
           p.telefono, p.estado,
           CASE WHEN p.es_demo THEN 'DEMO' ELSE 'Migrado' END AS origen,
           p.creado, p.actualizado
    FROM personas p
"""


class PersonaRepository:
    def __init__(self):
        self.db = Database()

    def obtener_todos(self):
        with self.db.cursor() as cursor:
            cursor.execute(_SELECT + " WHERE p.estado <> 'Inactivo' ORDER BY p.apellidos, p.nombres")
            return serializar_dato(cursor.fetchall())

    def obtener_por_id(self, persona_id: int):
        with self.db.cursor() as cursor:
            cursor.execute(_SELECT + " WHERE p.persona_id=%s AND p.estado <> 'Inactivo'", (persona_id,))
            return serializar_dato(cursor.fetchone())

    def crear(self, persona: Persona):
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                """
                INSERT INTO personas (documento,nombres,apellidos,correo,telefono,estado)
                VALUES (%s,%s,%s,%s,%s,%s) RETURNING persona_id
                """,
                (
                    _documento(persona.documento),
                    persona.nombres.strip(),
                    persona.apellidos.strip(),
                    persona.correo.strip().lower(),
                    persona.telefono,
                    persona.estado,
                ),
            )
            return cursor.fetchone()["persona_id"]

    def actualizar(self, persona_id: int, persona: Persona):
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                """
                UPDATE personas SET documento=%s,nombres=%s,apellidos=%s,correo=%s,
                    telefono=%s,estado=%s,actualizado=CURRENT_TIMESTAMP
                WHERE persona_id=%s RETURNING persona_id
                """,
                (
                    _documento(persona.documento),
                    persona.nombres.strip(),
                    persona.apellidos.strip(),
                    persona.correo.strip().lower(),
                    persona.telefono,
                    persona.estado,
                    persona_id,
                ),
            )
            return cursor.fetchone() is not None

    def eliminar(self, persona_id: int):
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                "UPDATE tutores_academicos SET estado='Inactivo', actualizado=CURRENT_TIMESTAMP WHERE persona_id=%s AND estado <> 'Inactivo'",
                (persona_id,),
            )
            cursor.execute(
                "UPDATE tutores_empresariales SET estado='Inactivo', actualizado=CURRENT_TIMESTAMP WHERE persona_id=%s AND estado <> 'Inactivo'",
                (persona_id,),
            )
            cursor.execute(
                "UPDATE personas SET estado='Inactivo', actualizado=CURRENT_TIMESTAMP WHERE persona_id=%s AND estado <> 'Inactivo' RETURNING persona_id",
                (persona_id,),
            )
            return "eliminada" if cursor.fetchone() else "no_encontrada"


def _documento(value: str) -> str:
    return " ".join(value.strip().upper().split())
