from app.core.database import Database, serializar_dato
from app.models.tutor_academico import TutorAcademico


_SELECT = """
    SELECT t.tutor_academico_id,t.persona_id,p.documento,p.nombres,p.apellidos,
           p.correo,p.telefono,t.cargo,t.programa_id,t.estado,
           CASE WHEN p.es_demo THEN 'DEMO' ELSE 'Registrado' END AS origen,
           t.creado,t.actualizado
    FROM tutores_academicos t JOIN personas p ON p.persona_id=t.persona_id
"""


class TutorAcademicoRepository:
    def __init__(self):
        self.db = Database()

    def obtener_todos(self):
        with self.db.cursor() as cursor:
            cursor.execute(_SELECT + " WHERE t.estado <> 'Inactivo' ORDER BY t.tutor_academico_id")
            return serializar_dato(cursor.fetchall())

    def obtener_por_id(self, tutor_academico_id: int):
        with self.db.cursor() as cursor:
            cursor.execute(_SELECT + " WHERE t.tutor_academico_id=%s AND t.estado <> 'Inactivo'", (tutor_academico_id,))
            return serializar_dato(cursor.fetchone())

    def obtener_por_programa(self, programa_id: int):
        with self.db.cursor() as cursor:
            cursor.execute(_SELECT + " WHERE t.programa_id=%s AND t.estado <> 'Inactivo' ORDER BY t.tutor_academico_id", (programa_id,))
            return serializar_dato(cursor.fetchall())

    def crear(self, tutor: TutorAcademico):
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                """
                INSERT INTO tutores_academicos
                    (persona_id,documento,nombres,apellidos,correo,telefono,cargo,programa_id)
                SELECT p.persona_id,p.documento,p.nombres,p.apellidos,p.correo,p.telefono,%s,%s
                FROM personas p WHERE p.persona_id=%s AND p.estado='Activo'
                RETURNING tutor_academico_id
                """,
                (tutor.cargo.strip(), tutor.programa_id, tutor.persona_id),
            )
            result = cursor.fetchone()
            return result["tutor_academico_id"] if result else None

    def actualizar(self, tutor_academico_id: int, tutor: TutorAcademico):
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                """
                UPDATE tutores_academicos t SET persona_id=p.persona_id,
                    documento=p.documento,nombres=p.nombres,apellidos=p.apellidos,
                    correo=p.correo,telefono=p.telefono,cargo=%s,programa_id=%s,
                    actualizado=CURRENT_TIMESTAMP
                FROM personas p WHERE t.tutor_academico_id=%s AND p.persona_id=%s AND p.estado='Activo'
                RETURNING t.tutor_academico_id
                """,
                (tutor.cargo.strip(), tutor.programa_id, tutor_academico_id, tutor.persona_id),
            )
            return cursor.fetchone() is not None

    def eliminar(self, tutor_academico_id: int):
        with self.db.cursor(commit=True) as cursor:
            cursor.execute(
                "UPDATE tutores_academicos SET estado='Inactivo', actualizado=CURRENT_TIMESTAMP WHERE tutor_academico_id=%s AND estado <> 'Inactivo' RETURNING tutor_academico_id",
                (tutor_academico_id,),
            )
            return cursor.fetchone() is not None
