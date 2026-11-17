import json
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase.pdfmetrics import stringWidth

ROOT = Path(__file__).resolve().parents[1]
META = json.loads((ROOT / ".access_schema.json").read_text(encoding="utf-8"))
OUT = ROOT / "Diagrama_Relaciones_Practicas_Imprimir.pdf"

# A1 horizontal: 841 x 594 mm
PAGE_W, PAGE_H = 2383.94, 1683.78
BOX_W = 500
ROW_Y = {"base": 1280, "relaciones": 910, "proceso": 540, "salidas": 170}
COL_X = [72, 647, 1222, 1797]
PLACEMENT = {
    "programas": (COL_X[0], ROW_Y["base"]),
    "empresas": (COL_X[1], ROW_Y["base"]),
    "personas": (COL_X[2], ROW_Y["base"]),
    "roles": (COL_X[3], ROW_Y["base"]),
    "estudiantes": (COL_X[0], ROW_Y["relaciones"]),
    "convenios": (COL_X[1], ROW_Y["relaciones"]),
    "tutores_academicos": (COL_X[2], ROW_Y["relaciones"]),
    "roles_modulos": (COL_X[3], ROW_Y["relaciones"]),
    "practicas": (COL_X[1], ROW_Y["proceso"]),
    "tutores_empresariales": (COL_X[2], ROW_Y["proceso"]),
    "modulos": (COL_X[3], ROW_Y["proceso"]),
    "seguimientos": (COL_X[0], ROW_Y["salidas"]),
    "documentos": (COL_X[1], ROW_Y["salidas"]),
    "evaluaciones": (COL_X[2], ROW_Y["salidas"]),
    "usuarios_sistema": (COL_X[3], ROW_Y["salidas"]),
}
HEADER_H = 34
FIELD_H = 18
BOX_PAD = 12

columns = {}
for col in META["columns"]:
    columns.setdefault(col["table_name"], []).append(col)
fk_pairs = {(x["table_name"], x["column_name"]) for x in META["foreign_keys"]}
table_heights = {t: HEADER_H + BOX_PAD + FIELD_H * len(fields) + 8 for t, fields in columns.items()}
boxes = {}
for t, (x, y) in PLACEMENT.items():
    h = table_heights[t]
    boxes[t] = (x, y, BOX_W, h)

# Color key by functional layer
layer_colors = {
    "programas": "#3768D8", "empresas": "#E39731", "personas": "#8953C6",
    "roles": "#D85858", "estudiantes": "#3768D8", "convenios": "#E39731",
    "tutores_academicos": "#8953C6", "roles_modulos": "#D85858",
    "practicas": "#2D9A78", "tutores_empresariales": "#8953C6",
    "modulos": "#D85858", "seguimientos": "#2D9A78", "documentos": "#2D9A78",
    "evaluaciones": "#2D9A78", "usuarios_sistema": "#D85858",
}

c = canvas.Canvas(str(OUT), pagesize=(PAGE_W, PAGE_H), pageCompression=1)
c.setTitle("Diagrama de relaciones del sistema de prácticas profesionales")
c.setAuthor("Sistema de gestión de prácticas profesionales")

# Background and title
c.setFillColor(HexColor("#F5F7FB"))
c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
c.setFillColor(HexColor("#14243D"))
c.setFont("Helvetica-Bold", 28)
c.drawString(72, PAGE_H - 56, "Modelo relacional del sistema de prácticas")
c.setFillColor(HexColor("#53647D"))
c.setFont("Helvetica", 13)
c.drawString(72, PAGE_H - 82, "Tablas, claves y relaciones entre los procesos académicos, las prácticas y los permisos por rol")
c.setFillColor(HexColor("#3768D8"))
c.roundRect(PAGE_W - 510, PAGE_H - 83, 438, 32, 14, fill=1, stroke=0)
c.setFillColor(white)
c.setFont("Helvetica-Bold", 10)
c.drawCentredString(PAGE_W - 291, PAGE_H - 72, "DIAGRAMA COMPLETO  ·  15 TABLAS  ·  20 RELACIONES")

# Layer labels
for key, text in [("base", "1  ENTIDADES PRINCIPALES"), ("relaciones", "2  RELACIONES Y ASIGNACIONES"), ("proceso", "3  PRÁCTICAS Y SEGURIDAD"), ("salidas", "4  REGISTROS ASOCIADOS")]:
    row_tables = [t for t, (x, y) in PLACEMENT.items() if y == ROW_Y[key]]
    y = ROW_Y[key] + max(table_heights[t] for t in row_tables) + 12
    c.setFillColor(HexColor("#8190A6"))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(72, y, text)

def edge_point(box, side, offset=0):
    x, y, w, h = box
    if side == "top": return (x + w * 0.5 + offset, y + h)
    if side == "bottom": return (x + w * 0.5 + offset, y)
    if side == "left": return (x, y + h * 0.5 + offset)
    return (x + w, y + h * 0.5 + offset)

# Draw all FK connections behind table boxes.
# Curved strokes preserve direction and make crossing relationships easier to follow.
for fk in META["foreign_keys"]:
    parent, child = fk["foreign_table"], fk["table_name"]
    if parent not in boxes or child not in boxes:
        continue
    pb, cb = boxes[parent], boxes[child]
    px, py, pw, ph = pb
    cx, cy, cw, ch = cb
    pc = (px + pw / 2, py + ph / 2)
    cc = (cx + cw / 2, cy + ch / 2)
    dx, dy = cc[0] - pc[0], cc[1] - pc[1]
    if abs(dx) > abs(dy) * 1.05:
        pside, cside = ("right", "left") if dx > 0 else ("left", "right")
        p = edge_point(pb, pside)
        q = edge_point(cb, cside)
        bend = max(42, abs(q[0] - p[0]) * 0.32)
        sign = 1 if dx > 0 else -1
        cp1 = (p[0] + sign * bend, p[1])
        cp2 = (q[0] - sign * bend, q[1])
    else:
        pside, cside = ("bottom", "top") if dy < 0 else ("top", "bottom")
        p = edge_point(pb, pside)
        q = edge_point(cb, cside)
        bend = max(36, abs(q[1] - p[1]) * 0.32)
        sign = -1 if dy < 0 else 1
        cp1 = (p[0], p[1] + sign * bend)
        cp2 = (q[0], q[1] - sign * bend)
    c.setStrokeColor(HexColor("#9DAEC3"))
    c.setLineWidth(1.15)
    path = c.beginPath()
    path.moveTo(*p)
    path.curveTo(*cp1, *cp2, *q)
    c.drawPath(path, stroke=1, fill=0)
    # Small terminal dot on the foreign-key table end.
    c.setFillColor(HexColor("#62748B"))
    c.circle(q[0], q[1], 2.6, stroke=0, fill=1)

# Draw cards with every real database column.
for table, (x, y, w, h) in boxes.items():
    accent = HexColor(layer_colors[table])
    c.setFillColor(white)
    c.setStrokeColor(HexColor("#D7DFEA"))
    c.setLineWidth(0.8)
    c.roundRect(x, y, w, h, 10, fill=1, stroke=1)
    c.setFillColor(accent)
    c.roundRect(x, y + h - HEADER_H, w, HEADER_H, 10, fill=1, stroke=0)
    c.rect(x, y + h - HEADER_H, w, 10, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(x + 14, y + h - 22, table)
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor("#75849A"))
    fields = columns[table]
    c.drawRightString(x + w - 12, y + h - 22, f"{len(fields)} campos")
    field_y = y + h - HEADER_H - BOX_PAD - 12
    for fld in fields:
        name = fld["column_name"]
        is_pk = bool(fld["is_pk"])
        is_fk = (table, name) in fk_pairs
        marks = "PK · FK" if is_pk and is_fk else ("PK" if is_pk else ("FK" if is_fk else ""))
        c.setFillColor(HexColor("#26364D") if (is_pk or is_fk) else HexColor("#526278"))
        c.setFont("Helvetica-Bold" if (is_pk or is_fk) else "Helvetica", 9.2)
        c.drawString(x + 15, field_y, name)
        if marks:
            tag_color = HexColor("#3768D8") if is_pk else HexColor("#2D8A73")
            tag_w = 42 if marks == "PK · FK" else 25
            c.setFillColor(tag_color)
            c.roundRect(x + w - tag_w - 12, field_y - 3, tag_w, 13, 5, fill=1, stroke=0)
            c.setFillColor(white)
            c.setFont("Helvetica-Bold", 6.6)
            c.drawCentredString(x + w - tag_w / 2 - 12, field_y + 1, marks)
        field_y -= FIELD_H

# Compact legend, kept above the cards so every table remains visible.
c.setFillColor(HexColor("#53647D"))
c.setFont("Helvetica", 8.5)
c.drawString(72, PAGE_H - 111, "PK = clave principal     FK = clave foránea     1:N = una fila principal puede conectarse con varias filas dependientes")

# Footer and print setup note
c.setFillColor(HexColor("#53647D"))
c.setFont("Helvetica", 8)
c.drawString(72, 55, "Fuente: estructura real de la base PostgreSQL local. Las líneas muestran las 20 relaciones registradas.")
c.drawString(72, 40, "Tamaño recomendado de impresión: A1 horizontal, escala 100%. Para impresoras menores, usar impresión tipo póster o mosaico.")
c.setFillColor(HexColor("#8190A6"))
c.drawRightString(PAGE_W - 72, 40, "Permisos: roles - roles_modulos - modulos  |  Jerarquía: nivel_jerarquia")

c.showPage()
c.save()
print(OUT)

