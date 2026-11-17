from app.core.database import Database, serializar_dato


class RolRepository:
    def __init__(self):
        self.db = Database()

    def obtener_todos(self):
        with self.db.cursor() as cursor:
            cursor.execute("SELECT * FROM roles WHERE estado = 'Activo' ORDER BY rol_id ASC;")
            return serializar_dato(cursor.fetchall())

    def obtener_por_id(self, rol_id: int):
        with self.db.cursor() as cursor:
            cursor.execute("SELECT * FROM roles WHERE rol_id = %s;", (rol_id,))
            return serializar_dato(cursor.fetchone())

    def obtener_modulos_por_rol(self, rol_id: int):
        query = """
            SELECT
                rm.rol_modulo_id,
                rm.rol_id,
                rm.modulo_id,
                m.nombre AS modulo_nombre,
                m.codigo AS modulo_codigo,
                m.ruta AS modulo_ruta,
                m.descripcion AS modulo_descripcion,
                rm.puede_crear,
                rm.puede_leer,
                rm.puede_actualizar,
                rm.puede_eliminar,
                rm.estado
            FROM roles_modulos rm
            JOIN modulos m ON rm.modulo_id = m.modulo_id
            WHERE rm.rol_id = %s AND rm.estado = 'Activo' AND m.estado = 'Activo'
            ORDER BY m.modulo_id ASC;
        """
        with self.db.cursor() as cursor:
            cursor.execute(query, (rol_id,))
            return serializar_dato(cursor.fetchall())
