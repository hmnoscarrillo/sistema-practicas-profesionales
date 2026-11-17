from datetime import date, datetime
from email.message import EmailMessage
from io import BytesIO
import os
import re
import smtplib
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from pydantic import BaseModel, Field
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.database import Database, serializar_dato

router = APIRouter(prefix="/reportes", tags=["Reportes"])

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

REPORT_COLUMNS = [
    ("estudiante", "Estudiante"),
    ("documento", "Documento"),
    ("programa", "Programa"),
    ("facultad", "Facultad"),
    ("empresa", "Empresa"),
    ("nit_empresa", "NIT"),
    ("ciudad", "Ciudad"),
    ("convenio", "Convenio"),
    ("tutor_academico", "Tutor Académico"),
    ("tutor_empresarial", "Tutor Empresarial"),
    ("cargo", "Cargo"),
    ("modalidad", "Modalidad"),
    ("fecha_inicio", "Inicio"),
    ("fecha_fin", "Finaliza"),
    ("nota_final", "Nota"),
    ("estado", "Estado"),
]


class EnviarCorreoRequest(BaseModel):
    destinatario: str = Field(min_length=5, max_length=150)
    asunto: str = Field(default="Reporte de Prácticas Profesionales", min_length=3, max_length=200)
    mensaje: Optional[str] = "Adjunto encontrarás el reporte institucional de prácticas profesionales."
    formato: str = Field(default="pdf")
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None
    programa: Optional[str] = None
    empresa: Optional[str] = None
    estado: Optional[str] = None
    modalidad: Optional[str] = None


def _consultar_reporte(
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    programa: Optional[str] = None,
    empresa: Optional[str] = None,
    estado: Optional[str] = None,
    modalidad: Optional[str] = None,
) -> list[dict]:
    if fecha_desde and fecha_hasta and fecha_hasta < fecha_desde:
        raise HTTPException(
            status_code=422,
            detail="La fecha final no puede ser anterior a la fecha inicial.",
        )

    clauses = ["COALESCE(pr.estado, 'En proceso') NOT IN ('Inactiva', 'Inactivo')"]
    params: list = []

    if fecha_desde:
        clauses.append("pr.fecha_inicio >= %s")
        params.append(fecha_desde)
    if fecha_hasta:
        clauses.append("pr.fecha_fin <= %s")
        params.append(fecha_hasta)
    if programa:
        clauses.append("lower(trim(prog.nombre)) = lower(trim(%s))")
        params.append(programa)
    if empresa:
        clauses.append("lower(trim(emp.nombre)) = lower(trim(%s))")
        params.append(empresa)
    if estado:
        clauses.append("lower(trim(pr.estado)) = lower(trim(%s))")
        params.append(estado)
    if modalidad:
        clauses.append("lower(trim(pr.modalidad)) = lower(trim(%s))")
        params.append(modalidad)

    where_sql = " AND ".join(clauses)

    # Cruza 7 tablas relacionadas (practicas, estudiantes, programas, empresas, convenios,
    # tutores + personas, evaluaciones) sin devolver ningún identificador (*_id).
    query = f"""
        SELECT
            trim(est.nombres || ' ' || est.apellidos) AS estudiante,
            est.documento AS documento,
            prog.nombre AS programa,
            prog.facultad AS facultad,
            emp.nombre AS empresa,
            emp.nit AS nit_empresa,
            emp.ciudad AS ciudad,
            conv.codigo AS convenio,
            COALESCE(trim(pa.nombres || ' ' || pa.apellidos), 'Sin asignar') AS tutor_academico,
            COALESCE(trim(pe.nombres || ' ' || pe.apellidos), 'Sin asignar') AS tutor_empresarial,
            pr.cargo AS cargo,
            pr.modalidad AS modalidad,
            pr.fecha_inicio AS fecha_inicio,
            pr.fecha_fin AS fecha_fin,
            ev.nota_final AS nota_final,
            pr.estado AS estado
        FROM practicas pr
        JOIN estudiantes est ON est.estudiante_id = pr.estudiante_id
        JOIN programas prog ON prog.programa_id = pr.programa_id
        JOIN empresas emp ON emp.empresa_id = pr.empresa_id
        JOIN convenios conv ON conv.convenio_id = pr.convenio_id
        LEFT JOIN tutores_academicos ta ON ta.tutor_academico_id = pr.tutor_academico_id
        LEFT JOIN personas pa ON pa.persona_id = ta.persona_id
        LEFT JOIN tutores_empresariales te ON te.tutor_empresarial_id = pr.tutor_empresarial_id
        LEFT JOIN personas pe ON pe.persona_id = te.persona_id
        LEFT JOIN LATERAL (
            SELECT e.nota_final
            FROM evaluaciones e
            WHERE e.practica_id = pr.practica_id
              AND COALESCE(e.estado, 'Activo') <> 'Inactivo'
            ORDER BY e.fecha_evaluacion DESC, e.evaluacion_id DESC
            LIMIT 1
        ) ev ON TRUE
        WHERE {where_sql}
        ORDER BY pr.fecha_inicio DESC, estudiante ASC;
    """

    with Database().cursor() as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return serializar_dato(rows)


def _resumen_criterios(
    fecha_desde: Optional[date],
    fecha_hasta: Optional[date],
    programa: Optional[str],
    empresa: Optional[str],
    estado: Optional[str],
    modalidad: Optional[str],
) -> str:
    partes = []
    if fecha_desde or fecha_hasta:
        desde_txt = fecha_desde.isoformat() if fecha_desde else "Inicio"
        hasta_txt = fecha_hasta.isoformat() if fecha_hasta else "Actual"
        partes.append(f"Periodo: {desde_txt} a {hasta_txt}")
    if programa:
        partes.append(f"Programa: {programa}")
    if empresa:
        partes.append(f"Empresa: {empresa}")
    if estado:
        partes.append(f"Estado: {estado}")
    if modalidad:
        partes.append(f"Modalidad: {modalidad}")
    return " | ".join(partes) if partes else "Todos los registros activos"


def _generar_pdf_bytes(registros: list[dict], criterios_texto: str) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=14 * mm,
        bottomMargin=16 * mm,
        title="Reporte de Prácticas Profesionales",
        author="Sistema de Gestión de Prácticas Profesionales",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=colors.white,
        spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#DCE8FF"),
    )
    meta_style = ParagraphStyle(
        "ReportMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#243245"),
    )
    header_cell_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.2,
        leading=9,
        textColor=colors.white,
    )
    cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.0,
        leading=9,
        textColor=colors.HexColor("#1F2B3A"),
    )

    generado = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Encabezado institucional estilizado
    banner = Table(
        [
            [
                Paragraph("REPORTE DE PRÁCTICAS PROFESIONALES", title_style),
            ],
            [
                Paragraph(
                    f"Portal Institucional de Prácticas · Generado el {generado} · Sin identificadores internos",
                    subtitle_style,
                ),
            ],
        ],
        colWidths=[273 * mm],
    )
    banner.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#142641")),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
            ]
        )
    )

    meta_box = Table(
        [
            [
                Paragraph(f"<b>Criterios aplicados:</b> {criterios_texto}", meta_style),
                Paragraph(f"<b>Total registros:</b> {len(registros)}", meta_style),
            ]
        ],
        colWidths=[225 * mm, 48 * mm],
    )
    meta_box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EEF3FC")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#C7D6F5")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    # Selección compacta y legible de columnas para paisaje A4 (sin IDs)
    pdf_cols = [
        ("estudiante", "Estudiante", 28 * mm),
        ("documento", "Documento", 18 * mm),
        ("programa", "Programa", 26 * mm),
        ("empresa", "Empresa", 26 * mm),
        ("convenio", "Convenio", 17 * mm),
        ("tutor_academico", "Tutor Académico", 25 * mm),
        ("tutor_empresarial", "Tutor Empresarial", 25 * mm),
        ("cargo", "Cargo", 24 * mm),
        ("modalidad", "Modalidad", 17 * mm),
        ("fecha_inicio", "Inicio", 17 * mm),
        ("fecha_fin", "Fin", 17 * mm),
        ("nota_final", "Nota", 12 * mm),
        ("estado", "Estado", 21 * mm),
    ]

    table_data = [[Paragraph(label, header_cell_style) for _, label, _ in pdf_cols]]
    for row in registros:
        rendered_row = []
        for key, _, _ in pdf_cols:
            val = row.get(key)
            if key == "nota_final":
                txt = f"{float(val):.1f}" if val is not None else "—"
            elif val is None or val == "":
                txt = "—"
            else:
                txt = str(val)
            rendered_row.append(Paragraph(txt, cell_style))
        table_data.append(rendered_row)

    if not registros:
        table_data.append([Paragraph("No se encontraron registros para los criterios seleccionados.", cell_style)] + [Paragraph("", cell_style)] * (len(pdf_cols) - 1))

    data_table = Table(table_data, colWidths=[w for _, _, w in pdf_cols], repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2552D0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#D5DFEF")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for idx in range(1, len(table_data)):
        bg = colors.white if idx % 2 == 1 else colors.HexColor("#F4F7FD")
        style_cmds.append(("BACKGROUND", (0, idx), (-1, idx), bg))
    if not registros:
        style_cmds.append(("SPAN", (0, 1), (-1, 1)))

    data_table.setStyle(TableStyle(style_cmds))

    def draw_footer(canvas, current_doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
        canvas.setLineWidth(0.6)
        canvas.line(12 * mm, 12 * mm, landscape(A4)[0] - 12 * mm, 12 * mm)
        canvas.setFont("Helvetica", 7.8)
        canvas.setFillColor(colors.HexColor("#526071"))
        canvas.drawString(
            12 * mm,
            8 * mm,
            f"Sistema de Gestión de Prácticas Profesionales · Generado: {generado} · Reporte sin identificadores internos",
        )
        canvas.drawRightString(
            landscape(A4)[0] - 12 * mm,
            8 * mm,
            f"Página {current_doc.page}",
        )
        canvas.restoreState()

    story = [banner, Spacer(1, 4 * mm), meta_box, Spacer(1, 5 * mm), data_table]
    doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)
    return buffer.getvalue()


def _generar_excel_bytes(registros: list[dict], criterios_texto: str) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Reporte Prácticas"

    total_cols = len(REPORT_COLUMNS)
    last_col_letter = get_column_letter(total_cols)
    generado = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Encabezado institucional
    ws.merge_cells(f"A1:{last_col_letter}1")
    ws["A1"] = "REPORTE INSTITUCIONAL DE PRÁCTICAS PROFESIONALES"
    ws["A1"].font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
    ws["A1"].fill = PatternFill(start_color="142641", end_color="142641", fill_type="solid")
    ws["A1"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[1].height = 28

    ws.merge_cells(f"A2:{last_col_letter}2")
    ws["A2"] = f"Generado: {generado}  |  Criterios: {criterios_texto}"
    ws["A2"].font = Font(name="Calibri", size=10, italic=True, color="1F2B3A")
    ws["A2"].fill = PatternFill(start_color="EEF3FC", end_color="EEF3FC", fill_type="solid")
    ws["A2"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[2].height = 22

    header_row = 4
    header_fill = PatternFill(start_color="2552D0", end_color="2552D0", fill_type="solid")
    header_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    thin_side = Side(style="thin", color="D5DFEF")
    cell_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

    for col_idx, (_, label) in enumerate(REPORT_COLUMNS, start=1):
        cell = ws.cell(row=header_row, column=col_idx, value=label)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = cell_border
    ws.row_dimensions[header_row].height = 24

    zebra_fill = PatternFill(start_color="F5F8FE", end_color="F5F8FE", fill_type="solid")
    white_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    body_font = Font(name="Calibri", size=10, color="1F2B3A")

    notas = []
    for row_offset, row in enumerate(registros, start=header_row + 1):
        fill = white_fill if row_offset % 2 == 1 else zebra_fill
        for col_idx, (key, _) in enumerate(REPORT_COLUMNS, start=1):
            val = row.get(key)
            if key == "nota_final" and val is not None:
                val = float(val)
                notas.append(val)
            cell = ws.cell(row=row_offset, column=col_idx, value=val if val not in (None, "") else "—")
            cell.fill = fill
            cell.font = body_font
            cell.border = cell_border
            if key == "nota_final" and isinstance(val, float):
                cell.number_format = "0.0"
                cell.alignment = Alignment(horizontal="right", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        ws.row_dimensions[row_offset].height = 20

    # Pie del reporte
    footer_row = header_row + len(registros) + 2
    ws.merge_cells(f"A{footer_row}:{last_col_letter}{footer_row}")
    promedio = f"{sum(notas) / len(notas):.2f}" if notas else "—"
    ws[f"A{footer_row}"] = (
        f"Total registros exportados: {len(registros)}  |  Promedio de nota final: {promedio}  |  Portal de Prácticas Profesionales"
    )
    ws[f"A{footer_row}"].font = Font(name="Calibri", size=10, bold=True, color="142641")
    ws[f"A{footer_row}"].fill = PatternFill(start_color="E8F0FE", end_color="E8F0FE", fill_type="solid")
    ws[f"A{footer_row}"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[footer_row].height = 22

    # Ajuste automático de anchos
    for col_idx, (key, label) in enumerate(REPORT_COLUMNS, start=1):
        max_len = max(
            [len(label)] + [len(str(row.get(key) or "")) for row in registros]
        )
        ws.column_dimensions[get_column_letter(col_idx)].width = min(max(max_len + 4, 13), 34)

    ws.freeze_panes = "A5"
    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
    ws.page_setup.paperSize = ws.PAPERSIZE_A4

    out = BytesIO()
    wb.save(out)
    return out.getvalue()


@router.get("/filtros")
def obtener_filtros_reportes():
    with Database().cursor() as cursor:
        cursor.execute("SELECT nombre FROM programas WHERE estado <> 'Inactivo' ORDER BY nombre ASC;")
        programas = [r["nombre"] for r in cursor.fetchall()]

        cursor.execute("SELECT nombre FROM empresas WHERE estado NOT IN ('Inactiva', 'Inactivo') ORDER BY nombre ASC;")
        empresas = [r["nombre"] for r in cursor.fetchall()]

        cursor.execute(
            """
            SELECT DISTINCT trim(estado) AS estado
            FROM practicas
            WHERE COALESCE(estado, '') NOT IN ('Inactiva', 'Inactivo')
              AND estado IS NOT NULL AND trim(estado) <> ''
            ORDER BY 1;
            """
        )
        estados = [r["estado"] for r in cursor.fetchall()]

        cursor.execute(
            """
            SELECT DISTINCT trim(modalidad) AS modalidad
            FROM practicas
            WHERE COALESCE(estado, '') NOT IN ('Inactiva', 'Inactivo')
              AND modalidad IS NOT NULL AND trim(modalidad) <> ''
            ORDER BY 1;
            """
        )
        modalidades = [r["modalidad"] for r in cursor.fetchall()]

    return {
        "programas": programas,
        "empresas": empresas,
        "estados": estados,
        "modalidades": modalidades,
    }


@router.get("/practicas")
def consultar_reporte_practicas(
    fecha_desde: Optional[date] = Query(default=None),
    fecha_hasta: Optional[date] = Query(default=None),
    programa: Optional[str] = Query(default=None),
    empresa: Optional[str] = Query(default=None),
    estado: Optional[str] = Query(default=None),
    modalidad: Optional[str] = Query(default=None),
):
    registros = _consultar_reporte(fecha_desde, fecha_hasta, programa, empresa, estado, modalidad)
    criterios = _resumen_criterios(fecha_desde, fecha_hasta, programa, empresa, estado, modalidad)
    return {
        "generado": datetime.now().isoformat(timespec="minutes"),
        "criterios": criterios,
        "total": len(registros),
        "columnas": [{"key": k, "label": label} for k, label in REPORT_COLUMNS],
        "registros": registros,
    }


@router.get("/exportar/pdf")
def exportar_reporte_pdf(
    fecha_desde: Optional[date] = Query(default=None),
    fecha_hasta: Optional[date] = Query(default=None),
    programa: Optional[str] = Query(default=None),
    empresa: Optional[str] = Query(default=None),
    estado: Optional[str] = Query(default=None),
    modalidad: Optional[str] = Query(default=None),
):
    registros = _consultar_reporte(fecha_desde, fecha_hasta, programa, empresa, estado, modalidad)
    criterios = _resumen_criterios(fecha_desde, fecha_hasta, programa, empresa, estado, modalidad)
    pdf_bytes = _generar_pdf_bytes(registros, criterios)
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="reporte-practicas-profesionales.pdf"'},
    )


@router.get("/exportar/excel")
def exportar_reporte_excel(
    fecha_desde: Optional[date] = Query(default=None),
    fecha_hasta: Optional[date] = Query(default=None),
    programa: Optional[str] = Query(default=None),
    empresa: Optional[str] = Query(default=None),
    estado: Optional[str] = Query(default=None),
    modalidad: Optional[str] = Query(default=None),
):
    registros = _consultar_reporte(fecha_desde, fecha_hasta, programa, empresa, estado, modalidad)
    criterios = _resumen_criterios(fecha_desde, fecha_hasta, programa, empresa, estado, modalidad)
    xlsx_bytes = _generar_excel_bytes(registros, criterios)
    return StreamingResponse(
        BytesIO(xlsx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="reporte-practicas-profesionales.xlsx"'},
    )


@router.post("/enviar-correo")
def enviar_reporte_correo(body: EnviarCorreoRequest):
    destinatario = body.destinatario.strip()
    if not EMAIL_RE.match(destinatario):
        raise HTTPException(status_code=422, detail="Ingresa un correo electrónico válido.")
    if body.formato not in {"pdf", "excel", "ambos"}:
        raise HTTPException(status_code=422, detail="El formato debe ser pdf, excel o ambos.")

    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_from = os.getenv("SMTP_FROM", smtp_user).strip()

    if not smtp_user or not smtp_password:
        raise HTTPException(
            status_code=503,
            detail="Configura SMTP_USER y SMTP_PASSWORD en el servidor para habilitar el envío automático por correo.",
        )

    registros = _consultar_reporte(
        body.fecha_desde,
        body.fecha_hasta,
        body.programa,
        body.empresa,
        body.estado,
        body.modalidad,
    )
    criterios = _resumen_criterios(
        body.fecha_desde,
        body.fecha_hasta,
        body.programa,
        body.empresa,
        body.estado,
        body.modalidad,
    )

    msg = EmailMessage()
    msg["Subject"] = body.asunto.strip()
    msg["From"] = smtp_from
    msg["To"] = destinatario
    msg.set_content(
        f"{body.mensaje or ''}\n\n"
        f"Criterios aplicados: {criterios}\n"
        f"Total de registros incluidos: {len(registros)}\n"
        f"Generado el {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    )

    if body.formato in {"pdf", "ambos"}:
        pdf_bytes = _generar_pdf_bytes(registros, criterios)
        msg.add_attachment(
            pdf_bytes,
            maintype="application",
            subtype="pdf",
            filename="reporte-practicas-profesionales.pdf",
        )

    if body.formato in {"excel", "ambos"}:
        xlsx_bytes = _generar_excel_bytes(registros, criterios)
        msg.add_attachment(
            xlsx_bytes,
            maintype="application",
            subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="reporte-practicas-profesionales.xlsx",
        )

    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as server:
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"No se pudo entregar el correo vía SMTP: {exc}",
        ) from exc

    return {
        "mensaje": f"Reporte enviado correctamente a {destinatario}.",
        "registros": len(registros),
        "formato": body.formato,
    }
