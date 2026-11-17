"""Additive migration for shared people and their tutor assignments."""
from app.core.database import Database


def ensure_people_schema():
    conn = Database().get_connection()
    if conn is None:
        raise RuntimeError("Base de datos no disponible para preparar las personas y tutorías.")
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(hashtext('practicas_people_schema_v1'))")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS personas (
                    persona_id SERIAL PRIMARY KEY,
                    documento VARCHAR(30) NOT NULL,
                    nombres VARCHAR(100) NOT NULL,
                    apellidos VARCHAR(100) NOT NULL,
                    correo VARCHAR(150) NOT NULL,
                    telefono VARCHAR(30),
                    estado VARCHAR(20) NOT NULL DEFAULT 'Activo',
                    es_demo BOOLEAN NOT NULL DEFAULT FALSE,
                    creado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    actualizado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_personas_documento_normalizado ON personas (lower(trim(documento)))")
            cursor.execute("ALTER TABLE tutores_academicos ADD COLUMN IF NOT EXISTS persona_id INTEGER")
            cursor.execute("ALTER TABLE tutores_empresariales ADD COLUMN IF NOT EXISTS persona_id INTEGER")
            cursor.execute("""
                INSERT INTO personas (documento, nombres, apellidos, correo, telefono, estado)
                SELECT documento, nombres, apellidos, correo, telefono, estado
                FROM (
                    SELECT DISTINCT ON (lower(trim(documento))) documento, nombres, apellidos, correo, telefono, estado
                    FROM (
                        SELECT documento, nombres, apellidos, correo, telefono, estado, 1 AS prioridad FROM tutores_academicos
                        UNION ALL
                        SELECT documento, nombres, apellidos, correo, telefono, estado, 2 AS prioridad FROM tutores_empresariales
                    ) fuentes
                    ORDER BY lower(trim(documento)), prioridad
                ) unicas
                ON CONFLICT DO NOTHING
            """)
            cursor.execute("""
                UPDATE tutores_academicos t SET persona_id=p.persona_id
                FROM personas p WHERE lower(trim(t.documento))=lower(trim(p.documento)) AND t.persona_id IS NULL
            """)
            cursor.execute("""
                UPDATE tutores_empresariales t SET persona_id=p.persona_id
                FROM personas p WHERE lower(trim(t.documento))=lower(trim(p.documento)) AND t.persona_id IS NULL
            """)
            cursor.execute("SELECT COUNT(*) AS faltantes FROM tutores_academicos WHERE persona_id IS NULL")
            if cursor.fetchone()["faltantes"]:
                raise RuntimeError("Hay tutores académicos que no se pudieron relacionar con una persona.")
            cursor.execute("SELECT COUNT(*) AS faltantes FROM tutores_empresariales WHERE persona_id IS NULL")
            if cursor.fetchone()["faltantes"]:
                raise RuntimeError("Hay tutores empresariales que no se pudieron relacionar con una persona.")
            cursor.execute("ALTER TABLE tutores_academicos ALTER COLUMN persona_id SET NOT NULL")
            cursor.execute("ALTER TABLE tutores_empresariales ALTER COLUMN persona_id SET NOT NULL")
            cursor.execute("""
                DO $$ BEGIN
                    ALTER TABLE tutores_academicos ADD CONSTRAINT fk_tutores_academicos_persona
                    FOREIGN KEY (persona_id) REFERENCES personas(persona_id) ON DELETE RESTRICT;
                EXCEPTION WHEN duplicate_object THEN NULL; END $$
            """)
            cursor.execute("""
                DO $$ BEGIN
                    ALTER TABLE tutores_empresariales ADD CONSTRAINT fk_tutores_empresariales_persona
                    FOREIGN KEY (persona_id) REFERENCES personas(persona_id) ON DELETE RESTRICT;
                EXCEPTION WHEN duplicate_object THEN NULL; END $$
            """)
            cursor.execute("ALTER TABLE tutores_academicos DROP CONSTRAINT IF EXISTS tutores_academicos_documento_key")
            cursor.execute("ALTER TABLE tutores_academicos DROP CONSTRAINT IF EXISTS tutores_academicos_correo_key")
            cursor.execute("ALTER TABLE tutores_empresariales DROP CONSTRAINT IF EXISTS tutores_empresariales_documento_key")
            cursor.execute("ALTER TABLE tutores_empresariales DROP CONSTRAINT IF EXISTS tutores_empresariales_correo_key")
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_tutor_academico_persona_programa ON tutores_academicos (persona_id, programa_id)")
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_tutor_empresarial_persona_empresa ON tutores_empresariales (persona_id, empresa_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_tutores_academicos_persona ON tutores_academicos (persona_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_tutores_empresariales_persona ON tutores_empresariales (persona_id)")

            cursor.execute("""
                INSERT INTO modulos (nombre, codigo, ruta, descripcion, nivel_minimo_requerido, estado)
                VALUES ('Gestión de Personas', 'PERSONAS', '/personas', 'Directorio común de personas y sus cargos de tutoría', 1, 'Activo')
                ON CONFLICT (codigo) DO UPDATE SET nombre=EXCLUDED.nombre, ruta=EXCLUDED.ruta,
                    descripcion=EXCLUDED.descripcion, estado='Activo', actualizado=CURRENT_TIMESTAMP
            """)
            cursor.execute("""
                INSERT INTO roles_modulos (rol_id, modulo_id, puede_crear, puede_leer, puede_actualizar, puede_eliminar, estado)
                SELECT rm.rol_id, nuevo.modulo_id, rm.puede_crear, rm.puede_leer, rm.puede_actualizar, rm.puede_eliminar, 'Activo'
                FROM roles_modulos rm
                JOIN modulos origen ON origen.modulo_id=rm.modulo_id AND origen.codigo='TUTORES_ACADEMICOS'
                CROSS JOIN modulos nuevo
                WHERE nuevo.codigo='PERSONAS'
                ON CONFLICT (rol_id, modulo_id) DO NOTHING
            """)

            # One clearly fictional, visibly marked person demonstrates both assignments.
            cursor.execute("""
                INSERT INTO personas (documento, nombres, apellidos, correo, telefono, estado, es_demo)
                VALUES ('DEMO-TUTOR-001', 'DEMO', 'Persona compartida', 'tutor.demo@example.test', '0000000000', 'Activo', TRUE)
                ON CONFLICT DO NOTHING
            """)
            cursor.execute("SELECT persona_id, documento, nombres, apellidos, correo, telefono FROM personas WHERE lower(trim(documento))='demo-tutor-001'")
            demo = cursor.fetchone()
            cursor.execute("SELECT programa_id FROM programas WHERE estado='Activo' ORDER BY programa_id LIMIT 1")
            programa = cursor.fetchone()
            cursor.execute("SELECT empresa_id FROM empresas WHERE estado IN ('Activa','Activo') ORDER BY empresa_id LIMIT 1")
            empresa = cursor.fetchone()
            if programa:
                cursor.execute("""
                    INSERT INTO tutores_academicos (persona_id, documento, nombres, apellidos, correo, telefono, cargo, programa_id, estado)
                    SELECT %s, %s, %s, %s, %s, %s, 'Tutor académico (DEMO)', %s, 'Activo'
                    WHERE NOT EXISTS (SELECT 1 FROM tutores_academicos WHERE persona_id=%s AND programa_id=%s)
                """, (demo["persona_id"], demo["documento"], demo["nombres"], demo["apellidos"], demo["correo"], demo["telefono"], programa["programa_id"], demo["persona_id"], programa["programa_id"]))
            if empresa:
                cursor.execute("""
                    INSERT INTO tutores_empresariales (persona_id, documento, nombres, apellidos, correo, telefono, cargo, empresa_id, estado)
                    SELECT %s, %s, %s, %s, %s, %s, 'Tutor empresarial (DEMO)', %s, 'Activo'
                    WHERE NOT EXISTS (SELECT 1 FROM tutores_empresariales WHERE persona_id=%s AND empresa_id=%s)
                """, (demo["persona_id"], demo["documento"], demo["nombres"], demo["apellidos"], demo["correo"], demo["telefono"], empresa["empresa_id"], demo["persona_id"], empresa["empresa_id"]))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
