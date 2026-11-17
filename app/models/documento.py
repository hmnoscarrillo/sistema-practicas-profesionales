from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class Documento(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    documento_id: Optional[int] = None
    practica_id: int = Field(gt=0)
    nombre_documento: str = Field(min_length=1, max_length=180)
    tipo_documento: str = Field(min_length=1, max_length=80)
    fecha_subida: date
    ruta_archivo: Optional[str] = None
    estado: Optional[str] = "Pendiente"
