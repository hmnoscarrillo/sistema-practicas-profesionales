from app.core.database import Database, serializar_dato
from app.models.programa import Programa


class ProgramaRepository:
    def __init__(self):
        self.db = Database()

    def obtener_todos(self):
        with self.db.cursor() as cursor:
            cursor.execute("SELECT * FROM programas WHERE estado <> 'Inactivo' ORDER BY programa_id ASC;")
            return serializar_dato(cursor.fetchall())

    def obtener_por_id(self, programa_id: int):
        with self.db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM programas WHERE programa_id = %s AND estado <> 'Inactivo';",
                (programa_id,),
            )
            return serializar_dato(cursor.fetchone())

    def crear(self, programa: Programa):
        query = """
            INSERT INTO programas
            (nombre, facultad, nivel, duracion_semestres, estado)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING programa_id;
        """
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                query,
                (
                    programa.nombre,
                    programa.facultad,
                    programa.nivel,
                    programa.duracion_semestres,
                    programa.estado or "Activo",
                ),
            )
            return cursor.fetchone()["programa_id"]

    def actualizar(self, programa_id: int, programa: Programa):
        query = """
            UPDATE programas
            SET nombre = %s,
                facultad = %s,
                nivel = %s,
                duracion_semestres = %s,
                estado = %s,
                actualizado = CURRENT_TIMESTAMP
            WHERE programa_id = %s
            RETURNING programa_id;
        """
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                query,
                (
                    programa.nombre,
                    programa.facultad,
                    programa.nivel,
                    programa.duracion_semestres,
                    programa.estado or "Activo",
                    programa_id,
                ),
            )
            return cursor.fetchone() is not None

    def eliminar(self, programa_id: int):
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                "UPDATE programas SET estado='Inactivo', actualizado=CURRENT_TIMESTAMP WHERE programa_id = %s AND estado <> 'Inactivo' RETURNING programa_id;",
                (programa_id,),
            )
            return cursor.fetchone() is not None
