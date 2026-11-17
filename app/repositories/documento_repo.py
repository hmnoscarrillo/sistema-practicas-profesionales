from app.core.database import Database, serializar_dato
from app.models.documento import Documento


class DocumentoRepository:
    def __init__(self):
        self.db = Database()

    def obtener_todos(self):
        with self.db.cursor() as cursor:
            cursor.execute("SELECT * FROM documentos WHERE estado <> 'Inactivo' ORDER BY documento_id ASC;")
            return serializar_dato(cursor.fetchall())

    def obtener_por_id(self, documento_id: int):
        with self.db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM documentos WHERE documento_id = %s AND estado <> 'Inactivo';",
                (documento_id,),
            )
            return serializar_dato(cursor.fetchone())

    def obtener_por_practica(self, practica_id: int):
        with self.db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM documentos WHERE practica_id = %s AND estado <> 'Inactivo' ORDER BY documento_id ASC;",
                (practica_id,),
            )
            return serializar_dato(cursor.fetchall())

    def crear(self, documento: Documento):
        query = """
            INSERT INTO documentos
            (practica_id, nombre_documento, tipo_documento, fecha_subida, ruta_archivo, estado)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING documento_id;
        """
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                query,
                (
                    documento.practica_id,
                    documento.nombre_documento,
                    documento.tipo_documento,
                    documento.fecha_subida,
                    documento.ruta_archivo,
                    documento.estado or "Pendiente",
                ),
            )
            return cursor.fetchone()["documento_id"]

    def actualizar(self, documento_id: int, documento: Documento):
        query = """
            UPDATE documentos
            SET practica_id = %s,
                nombre_documento = %s,
                tipo_documento = %s,
                fecha_subida = %s,
                ruta_archivo = %s,
                estado = %s,
                actualizado = CURRENT_TIMESTAMP
            WHERE documento_id = %s
            RETURNING documento_id;
        """
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                query,
                (
                    documento.practica_id,
                    documento.nombre_documento,
                    documento.tipo_documento,
                    documento.fecha_subida,
                    documento.ruta_archivo,
                    documento.estado or "Pendiente",
                    documento_id,
                ),
            )
            return cursor.fetchone() is not None

    def eliminar(self, documento_id: int):
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                "UPDATE documentos SET estado='Inactivo', actualizado=CURRENT_TIMESTAMP WHERE documento_id = %s AND estado <> 'Inactivo' RETURNING documento_id;",
                (documento_id,),
            )
            return cursor.fetchone() is not None
