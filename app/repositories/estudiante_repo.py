from app.core.database import Database, serializar_dato
from app.models.estudiante import Estudiante


class EstudianteRepository:
    def __init__(self):
        self.db = Database()

    def obtener_todos(self):
        with self.db.cursor() as cursor:
            cursor.execute("SELECT * FROM estudiantes WHERE estado <> 'Inactivo' ORDER BY estudiante_id ASC;")
            return serializar_dato(cursor.fetchall())

    def obtener_por_id(self, estudiante_id: int):
        with self.db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM estudiantes WHERE estudiante_id = %s AND estado <> 'Inactivo';",
                (estudiante_id,),
            )
            return serializar_dato(cursor.fetchone())

    def obtener_por_programa(self, programa_id: int):
        with self.db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM estudiantes WHERE programa_id = %s AND estado <> 'Inactivo' ORDER BY estudiante_id ASC;",
                (programa_id,),
            )
            return serializar_dato(cursor.fetchall())

    def crear(self, estudiante: Estudiante):
        query = """
            INSERT INTO estudiantes
            (documento, nombres, apellidos, correo, telefono, semestre, programa_id, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING estudiante_id;
        """
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                query,
                (
                    estudiante.documento,
                    estudiante.nombres,
                    estudiante.apellidos,
                    estudiante.correo.lower(),
                    estudiante.telefono,
                    estudiante.semestre,
                    estudiante.programa_id,
                    estudiante.estado or "Activo",
                ),
            )
            return cursor.fetchone()["estudiante_id"]

    def actualizar(self, estudiante_id: int, estudiante: Estudiante):
        query = """
            UPDATE estudiantes
            SET documento = %s,
                nombres = %s,
                apellidos = %s,
                correo = %s,
                telefono = %s,
                semestre = %s,
                programa_id = %s,
                estado = %s,
                actualizado = CURRENT_TIMESTAMP
            WHERE estudiante_id = %s
            RETURNING estudiante_id;
        """
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                query,
                (
                    estudiante.documento,
                    estudiante.nombres,
                    estudiante.apellidos,
                    estudiante.correo.lower(),
                    estudiante.telefono,
                    estudiante.semestre,
                    estudiante.programa_id,
                    estudiante.estado or "Activo",
                    estudiante_id,
                ),
            )
            return cursor.fetchone() is not None

    def eliminar(self, estudiante_id: int):
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                "UPDATE estudiantes SET estado='Inactivo', actualizado=CURRENT_TIMESTAMP WHERE estudiante_id = %s AND estado <> 'Inactivo' RETURNING estudiante_id;",
                (estudiante_id,),
            )
            return cursor.fetchone() is not None
