from app.core.database import Database, serializar_dato
from app.models.evaluacion import Evaluacion


class EvaluacionRepository:
    def __init__(self):
        self.db = Database()

    def obtener_todos(self):
        with self.db.cursor() as cursor:
            cursor.execute("SELECT * FROM evaluaciones WHERE estado <> 'Inactivo' ORDER BY evaluacion_id ASC;")
            return serializar_dato(cursor.fetchall())

    def obtener_por_id(self, evaluacion_id: int):
        with self.db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM evaluaciones WHERE evaluacion_id = %s AND estado <> 'Inactivo';",
                (evaluacion_id,),
            )
            return serializar_dato(cursor.fetchone())

    def obtener_por_practica(self, practica_id: int):
        with self.db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM evaluaciones WHERE practica_id = %s AND estado <> 'Inactivo' ORDER BY evaluacion_id ASC;",
                (practica_id,),
            )
            return serializar_dato(cursor.fetchall())

    def crear(self, evaluacion: Evaluacion):
        query = """
            INSERT INTO evaluaciones
            (practica_id, fecha_evaluacion, evaluador, nota_academica, nota_empresarial, nota_final, comentarios, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING evaluacion_id;
        """
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                query,
                (
                    evaluacion.practica_id,
                    evaluacion.fecha_evaluacion,
                    evaluacion.evaluador,
                    evaluacion.nota_academica,
                    evaluacion.nota_empresarial,
                    evaluacion.nota_final,
                    evaluacion.comentarios,
                    evaluacion.estado or "Activo",
                ),
            )
            return cursor.fetchone()["evaluacion_id"]

    def actualizar(self, evaluacion_id: int, evaluacion: Evaluacion):
        query = """
            UPDATE evaluaciones
            SET practica_id = %s,
                fecha_evaluacion = %s,
                evaluador = %s,
                nota_academica = %s,
                nota_empresarial = %s,
                nota_final = %s,
                comentarios = %s,
                estado = %s,
                actualizado = CURRENT_TIMESTAMP
            WHERE evaluacion_id = %s
            RETURNING evaluacion_id;
        """
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                query,
                (
                    evaluacion.practica_id,
                    evaluacion.fecha_evaluacion,
                    evaluacion.evaluador,
                    evaluacion.nota_academica,
                    evaluacion.nota_empresarial,
                    evaluacion.nota_final,
                    evaluacion.comentarios,
                    evaluacion.estado or "Activo",
                    evaluacion_id,
                ),
            )
            return cursor.fetchone() is not None

    def eliminar(self, evaluacion_id: int):
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                "UPDATE evaluaciones SET estado='Inactivo', actualizado=CURRENT_TIMESTAMP WHERE evaluacion_id = %s AND estado <> 'Inactivo' RETURNING evaluacion_id;",
                (evaluacion_id,),
            )
            return cursor.fetchone() is not None
