from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class Seguimiento(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    seguimiento_id: Optional[int] = None
    practica_id: int = Field(gt=0)
    tutor_academico_id: int = Field(gt=0)
    fecha_seguimiento: date
    tipo: str = Field(min_length=1, max_length=60)
    observaciones: str = Field(min_length=1)
    estado: str = "Pendiente"
