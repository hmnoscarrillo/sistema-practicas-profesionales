from app.core.database import Database, serializar_dato
from app.models.practica import Practica


class PracticaRepository:
    def __init__(self):
        self.db = Database()

    def obtener_todos(self):
        with self.db.cursor() as cursor:
            cursor.execute("SELECT * FROM practicas WHERE estado NOT IN ('Inactiva','Inactivo') ORDER BY practica_id ASC;")
            return serializar_dato(cursor.fetchall())

    def obtener_por_id(self, practica_id: int):
        with self.db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM practicas WHERE practica_id = %s AND estado NOT IN ('Inactiva','Inactivo');",
                (practica_id,),
            )
            return serializar_dato(cursor.fetchone())

    def obtener_por_estudiante(self, estudiante_id: int):
        with self.db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM practicas WHERE estudiante_id = %s AND estado NOT IN ('Inactiva','Inactivo') ORDER BY practica_id ASC;",
                (estudiante_id,),
            )
            return serializar_dato(cursor.fetchall())

    def crear(self, practica: Practica):
        query = """
            INSERT INTO practicas
            (estudiante_id, empresa_id, programa_id, convenio_id, tutor_academico_id, tutor_empresarial_id, cargo, fecha_inicio, fecha_fin, modalidad, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING practica_id;
        """
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                query,
                (
                    practica.estudiante_id,
                    practica.empresa_id,
                    practica.programa_id,
                    practica.convenio_id,
                    practica.tutor_academico_id,
                    practica.tutor_empresarial_id,
                    practica.cargo,
                    practica.fecha_inicio,
                    practica.fecha_fin,
                    practica.modalidad,
                    practica.estado or "En proceso",
                ),
            )
            return cursor.fetchone()["practica_id"]

    def actualizar(self, practica_id: int, practica: Practica):
        query = """
            UPDATE practicas
            SET estudiante_id = %s,
                empresa_id = %s,
                programa_id = %s,
                convenio_id = %s,
                tutor_academico_id = %s,
                tutor_empresarial_id = %s,
                cargo = %s,
                fecha_inicio = %s,
                fecha_fin = %s,
                modalidad = %s,
                estado = %s,
                actualizado = CURRENT_TIMESTAMP
            WHERE practica_id = %s
            RETURNING practica_id;
        """
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                query,
                (
                    practica.estudiante_id,
                    practica.empresa_id,
                    practica.programa_id,
                    practica.convenio_id,
                    practica.tutor_academico_id,
                    practica.tutor_empresarial_id,
                    practica.cargo,
                    practica.fecha_inicio,
                    practica.fecha_fin,
                    practica.modalidad,
                    practica.estado or "En proceso",
                    practica_id,
                ),
            )
            return cursor.fetchone() is not None

    def eliminar(self, practica_id: int):
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                "UPDATE practicas SET estado='Inactiva', actualizado=CURRENT_TIMESTAMP WHERE practica_id = %s AND estado <> 'Inactiva' RETURNING practica_id;",
                (practica_id,),
            )
            return cursor.fetchone() is not None
