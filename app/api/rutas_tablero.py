from datetime import date
from typing import Optional

from fastapi import APIRouter, Query

from app.core.database import Database, serializar_dato

router = APIRouter(prefix="/tablero", tags=["Tablero"])


def _build_filters(
    programa: Optional[str],
    empresa: Optional[str],
    modalidad: Optional[str],
    estado: Optional[str],
    fecha_desde: Optional[date],
    fecha_hasta: Optional[date],
    alias_practica: str = "pr",
    alias_programa: str = "prog",
    alias_empresa: str = "emp",
):
    clauses = [f"COALESCE({alias_practica}.estado, 'En proceso') NOT IN ('Inactiva', 'Inactivo')"]
    params: list = []

    if programa:
        clauses.append(f"lower(trim({alias_programa}.nombre)) = lower(trim(%s))")
        params.append(programa)
    if empresa:
        clauses.append(f"lower(trim({alias_empresa}.nombre)) = lower(trim(%s))")
        params.append(empresa)
    if modalidad:
        clauses.append(f"lower(trim({alias_practica}.modalidad)) = lower(trim(%s))")
        params.append(modalidad)
    if estado:
        clauses.append(f"lower(trim({alias_practica}.estado)) = lower(trim(%s))")
        params.append(estado)
    if fecha_desde:
        clauses.append(f"{alias_practica}.fecha_inicio >= %s")
        params.append(fecha_desde)
    if fecha_hasta:
        clauses.append(f"{alias_practica}.fecha_fin <= %s")
        params.append(fecha_hasta)

    return " AND ".join(clauses), params


@router.get("/resumen")
def obtener_resumen_tablero(
    programa: Optional[str] = Query(default=None),
    empresa: Optional[str] = Query(default=None),
    modalidad: Optional[str] = Query(default=None),
    estado: Optional[str] = Query(default=None),
    fecha_desde: Optional[date] = Query(default=None),
    fecha_hasta: Optional[date] = Query(default=None),
):
    where_sql, params = _build_filters(programa, empresa, modalidad, estado, fecha_desde, fecha_hasta)

    with Database().cursor() as cursor:
        cursor.execute(
            f"""
            SELECT
                COUNT(DISTINCT pr.practica_id) AS total_practicas,
                COUNT(DISTINCT pr.practica_id) FILTER (
                    WHERE strpos(lower(COALESCE(pr.estado, '')), 'proceso') > 0
                ) AS practicas_en_proceso,
                COUNT(DISTINCT pr.practica_id) FILTER (
                    WHERE strpos(lower(COALESCE(pr.estado, '')), 'finaliz') > 0
                       OR strpos(lower(COALESCE(pr.estado, '')), 'complet') > 0
                ) AS practicas_finalizadas,
                COALESCE(ROUND(AVG(ev.nota_final)::numeric, 2), 0) AS promedio_evaluacion
            FROM practicas pr
            JOIN programas prog ON prog.programa_id = pr.programa_id
            JOIN empresas emp ON emp.empresa_id = pr.empresa_id
            LEFT JOIN LATERAL (
                SELECT e.nota_final
                FROM evaluaciones e
                WHERE e.practica_id = pr.practica_id
                  AND COALESCE(e.estado, 'Activo') <> 'Inactivo'
                ORDER BY e.fecha_evaluacion DESC, e.evaluacion_id DESC
                LIMIT 1
            ) ev ON TRUE
            WHERE {where_sql};
            """,
            params,
        )
        kpi_row = cursor.fetchone() or {}

        conv_clauses = ["COALESCE(c.estado, 'Vigente') <> 'Inactivo'"]
        conv_params: list = []
        if programa:
            conv_clauses.append("lower(trim(prog.nombre)) = lower(trim(%s))")
            conv_params.append(programa)
        if empresa:
            conv_clauses.append("lower(trim(emp.nombre)) = lower(trim(%s))")
            conv_params.append(empresa)
        conv_where = " AND ".join(conv_clauses)

        cursor.execute(
            f"""
            SELECT COUNT(*) FILTER (WHERE lower(COALESCE(c.estado, '')) = 'vigente') AS convenios_vigentes
            FROM convenios c
            JOIN programas prog ON prog.programa_id = c.programa_id
            JOIN empresas emp ON emp.empresa_id = c.empresa_id
            WHERE {conv_where};
            """,
            conv_params,
        )
        conv_kpi = cursor.fetchone() or {}

        cursor.execute(
            f"""
            SELECT COALESCE(pr.estado, 'Sin estado') AS label, COUNT(*) AS value
            FROM practicas pr
            JOIN programas prog ON prog.programa_id = pr.programa_id
            JOIN empresas emp ON emp.empresa_id = pr.empresa_id
            WHERE {where_sql}
            GROUP BY COALESCE(pr.estado, 'Sin estado')
            ORDER BY value DESC, label ASC;
            """,
            params,
        )
        por_estado = cursor.fetchall()

        cursor.execute(
            f"""
            SELECT COALESCE(pr.modalidad, 'Sin modalidad') AS label, COUNT(*) AS value
            FROM practicas pr
            JOIN programas prog ON prog.programa_id = pr.programa_id
            JOIN empresas emp ON emp.empresa_id = pr.empresa_id
            WHERE {where_sql}
            GROUP BY COALESCE(pr.modalidad, 'Sin modalidad')
            ORDER BY value DESC, label ASC;
            """,
            params,
        )
        por_modalidad = cursor.fetchall()

        cursor.execute(
            f"""
            SELECT prog.nombre AS label, COUNT(*) AS value
            FROM practicas pr
            JOIN programas prog ON prog.programa_id = pr.programa_id
            JOIN empresas emp ON emp.empresa_id = pr.empresa_id
            WHERE {where_sql}
            GROUP BY prog.nombre
            ORDER BY value DESC, label ASC
            LIMIT 6;
            """,
            params,
        )
        por_programa = cursor.fetchall()

        cursor.execute(
            f"""
            SELECT emp.nombre AS label, COUNT(*) AS value
            FROM practicas pr
            JOIN programas prog ON prog.programa_id = pr.programa_id
            JOIN empresas emp ON emp.empresa_id = pr.empresa_id
            WHERE {where_sql}
            GROUP BY emp.nombre
            ORDER BY value DESC, label ASC
            LIMIT 6;
            """,
            params,
        )
        por_empresa = cursor.fetchall()

        cursor.execute(
            f"""
            SELECT COALESCE(seg.tipo, 'General') AS label, COUNT(*) AS value
            FROM seguimientos seg
            JOIN practicas pr ON pr.practica_id = seg.practica_id
            JOIN programas prog ON prog.programa_id = pr.programa_id
            JOIN empresas emp ON emp.empresa_id = pr.empresa_id
            WHERE COALESCE(seg.estado, 'Pendiente') <> 'Inactivo'
              AND {where_sql}
            GROUP BY COALESCE(seg.tipo, 'General')
            ORDER BY value DESC, label ASC;
            """,
            params,
        )
        seguimientos_por_tipo = cursor.fetchall()

        cursor.execute(
            f"""
            SELECT COALESCE(c.estado, 'Sin estado') AS label, COUNT(*) AS value
            FROM convenios c
            JOIN programas prog ON prog.programa_id = c.programa_id
            JOIN empresas emp ON emp.empresa_id = c.empresa_id
            WHERE {conv_where}
            GROUP BY COALESCE(c.estado, 'Sin estado')
            ORDER BY value DESC, label ASC;
            """,
            conv_params,
        )
        convenios_por_estado = cursor.fetchall()

        cursor.execute(
            "SELECT nombre FROM programas WHERE estado <> 'Inactivo' ORDER BY nombre ASC;"
        )
        programas = [row["nombre"] for row in cursor.fetchall()]

        cursor.execute(
            "SELECT nombre FROM empresas WHERE estado NOT IN ('Inactiva', 'Inactivo') ORDER BY nombre ASC;"
        )
        empresas = [row["nombre"] for row in cursor.fetchall()]

        cursor.execute(
            """
            SELECT DISTINCT trim(modalidad) AS modalidad
            FROM practicas
            WHERE COALESCE(estado, '') NOT IN ('Inactiva', 'Inactivo')
              AND modalidad IS NOT NULL AND trim(modalidad) <> ''
            ORDER BY 1;
            """
        )
        modalidades = [row["modalidad"] for row in cursor.fetchall()]

        cursor.execute(
            """
            SELECT DISTINCT trim(estado) AS estado
            FROM practicas
            WHERE COALESCE(estado, '') NOT IN ('Inactiva', 'Inactivo')
              AND estado IS NOT NULL AND trim(estado) <> ''
            ORDER BY 1;
            """
        )
        estados = [row["estado"] for row in cursor.fetchall()]

    return serializar_dato(
        {
            "kpis": {
                "total_practicas": kpi_row.get("total_practicas", 0),
                "practicas_en_proceso": kpi_row.get("practicas_en_proceso", 0),
                "practicas_finalizadas": kpi_row.get("practicas_finalizadas", 0),
                "convenios_vigentes": conv_kpi.get("convenios_vigentes", 0),
                "promedio_evaluacion": kpi_row.get("promedio_evaluacion", 0),
            },
            "graficos": {
                "por_estado": por_estado,
                "por_modalidad": por_modalidad,
                "por_programa": por_programa,
                "por_empresa": por_empresa,
                "seguimientos_por_tipo": seguimientos_por_tipo,
                "convenios_por_estado": convenios_por_estado,
            },
            "filtros_disponibles": {
                "programas": programas,
                "empresas": empresas,
                "modalidades": modalidades,
                "estados": estados,
            },
        }
    )
