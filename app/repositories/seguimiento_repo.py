from app.core.database import Database, serializar_dato
from app.models.seguimiento import Seguimiento


class SeguimientoRepository:
    def __init__(self):
        self.db = Database()

    def obtener_todos(self):
        with self.db.cursor() as cursor:
            cursor.execute("SELECT * FROM seguimientos WHERE estado <> 'Inactivo' ORDER BY seguimiento_id ASC;")
            return serializar_dato(cursor.fetchall())

    def obtener_por_id(self, seguimiento_id: int):
        with self.db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM seguimientos WHERE seguimiento_id = %s AND estado <> 'Inactivo';",
                (seguimiento_id,),
            )
            return serializar_dato(cursor.fetchone())

    def obtener_por_practica(self, practica_id: int):
        with self.db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM seguimientos WHERE practica_id = %s AND estado <> 'Inactivo' ORDER BY seguimiento_id ASC;",
                (practica_id,),
            )
            return serializar_dato(cursor.fetchall())

    def crear(self, seguimiento: Seguimiento):
        query = """
            INSERT INTO seguimientos
            (practica_id, tutor_academico_id, fecha_seguimiento, tipo, observaciones, estado)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING seguimiento_id;
        """
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                query,
                (
                    seguimiento.practica_id,
                    seguimiento.tutor_academico_id,
                    seguimiento.fecha_seguimiento,
                    seguimiento.tipo,
                    seguimiento.observaciones,
                    seguimiento.estado,
                ),
            )
            return cursor.fetchone()["seguimiento_id"]

    def actualizar(self, seguimiento_id: int, seguimiento: Seguimiento):
        query = """
            UPDATE seguimientos
            SET practica_id = %s,
                tutor_academico_id = %s,
                fecha_seguimiento = %s,
                tipo = %s,
                observaciones = %s,
                estado = %s,
                actualizado = CURRENT_TIMESTAMP
            WHERE seguimiento_id = %s
            RETURNING seguimiento_id;
        """
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                query,
                (
                    seguimiento.practica_id,
                    seguimiento.tutor_academico_id,
                    seguimiento.fecha_seguimiento,
                    seguimiento.tipo,
                    seguimiento.observaciones,
                    seguimiento.estado,
                    seguimiento_id,
                ),
            )
            return cursor.fetchone() is not None

    def eliminar(self, seguimiento_id: int):
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                "UPDATE seguimientos SET estado='Inactivo', actualizado=CURRENT_TIMESTAMP WHERE seguimiento_id = %s AND estado <> 'Inactivo' RETURNING seguimiento_id;",
                (seguimiento_id,),
            )
            return cursor.fetchone() is not None
