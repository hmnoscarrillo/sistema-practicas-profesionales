from app.core.database import Database, serializar_dato
from app.models.empresa import Empresa


class EmpresaRepository:
    def __init__(self):
        self.db = Database()

    def obtener_todos(self):
        with self.db.cursor() as cursor:
            cursor.execute("SELECT * FROM empresas WHERE estado NOT IN ('Inactiva','Inactivo') ORDER BY empresa_id ASC;")
            return serializar_dato(cursor.fetchall())

    def obtener_por_id(self, empresa_id: int):
        with self.db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM empresas WHERE empresa_id = %s AND estado NOT IN ('Inactiva','Inactivo');",
                (empresa_id,),
            )
            return serializar_dato(cursor.fetchone())

    def crear(self, empresa: Empresa):
        query = """
            INSERT INTO empresas
            (nit, nombre, sector, ciudad, direccion, telefono, correo, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING empresa_id;
        """
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                query,
                (
                    empresa.nit,
                    empresa.nombre,
                    empresa.sector,
                    empresa.ciudad,
                    empresa.direccion,
                    empresa.telefono,
                    empresa.correo.lower() if empresa.correo else None,
                    empresa.estado or "Activa",
                ),
            )
            return cursor.fetchone()["empresa_id"]

    def actualizar(self, empresa_id: int, empresa: Empresa):
        query = """
            UPDATE empresas
            SET nit = %s,
                nombre = %s,
                sector = %s,
                ciudad = %s,
                direccion = %s,
                telefono = %s,
                correo = %s,
                estado = %s,
                actualizado = CURRENT_TIMESTAMP
            WHERE empresa_id = %s
            RETURNING empresa_id;
        """
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                query,
                (
                    empresa.nit,
                    empresa.nombre,
                    empresa.sector,
                    empresa.ciudad,
                    empresa.direccion,
                    empresa.telefono,
                    empresa.correo.lower() if empresa.correo else None,
                    empresa.estado or "Activa",
                    empresa_id,
                ),
            )
            return cursor.fetchone() is not None

    def eliminar(self, empresa_id: int):
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                "UPDATE empresas SET estado='Inactiva', actualizado=CURRENT_TIMESTAMP WHERE empresa_id = %s AND estado <> 'Inactiva' RETURNING empresa_id;",
                (empresa_id,),
            )
            return cursor.fetchone() is not None
