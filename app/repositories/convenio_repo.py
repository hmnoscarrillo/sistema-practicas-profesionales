from app.core.database import Database, serializar_dato
from app.models.convenio import Convenio


class ConvenioRepository:
    def __init__(self):
        self.db = Database()

    def obtener_todos(self):
        with self.db.cursor() as cursor:
            cursor.execute("SELECT * FROM convenios WHERE estado <> 'Inactivo' ORDER BY convenio_id ASC;")
            return serializar_dato(cursor.fetchall())

    def obtener_por_id(self, convenio_id: int):
        with self.db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM convenios WHERE convenio_id = %s AND estado <> 'Inactivo';",
                (convenio_id,),
            )
            return serializar_dato(cursor.fetchone())

    def obtener_por_empresa(self, empresa_id: int):
        with self.db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM convenios WHERE empresa_id = %s AND estado <> 'Inactivo' ORDER BY convenio_id ASC;",
                (empresa_id,),
            )
            return serializar_dato(cursor.fetchall())

    def crear(self, convenio: Convenio):
        query = """
            INSERT INTO convenios
            (codigo, empresa_id, programa_id, fecha_inicio, fecha_fin, estado)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING convenio_id;
        """
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                query,
                (
                    convenio.codigo,
                    convenio.empresa_id,
                    convenio.programa_id,
                    convenio.fecha_inicio,
                    convenio.fecha_fin,
                    convenio.estado or "Vigente",
                ),
            )
            return cursor.fetchone()["convenio_id"]

    def actualizar(self, convenio_id: int, convenio: Convenio):
        query = """
            UPDATE convenios
            SET codigo = %s,
                empresa_id = %s,
                programa_id = %s,
                fecha_inicio = %s,
                fecha_fin = %s,
                estado = %s,
                actualizado = CURRENT_TIMESTAMP
            WHERE convenio_id = %s
            RETURNING convenio_id;
        """
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                query,
                (
                    convenio.codigo,
                    convenio.empresa_id,
                    convenio.programa_id,
                    convenio.fecha_inicio,
                    convenio.fecha_fin,
                    convenio.estado or "Vigente",
                    convenio_id,
                ),
            )
            return cursor.fetchone() is not None

    def eliminar(self, convenio_id: int):
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                "UPDATE convenios SET estado='Inactivo', actualizado=CURRENT_TIMESTAMP WHERE convenio_id = %s AND estado <> 'Inactivo' RETURNING convenio_id;",
                (convenio_id,),
            )
            return cursor.fetchone() is not None
