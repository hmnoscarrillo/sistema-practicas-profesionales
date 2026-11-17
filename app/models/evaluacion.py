from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class Evaluacion(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    evaluacion_id: Optional[int] = None
    practica_id: int = Field(gt=0)
    fecha_evaluacion: date
    evaluador: str = Field(min_length=1, max_length=150)
    nota_academica: float = Field(ge=0, le=5)
    nota_empresarial: float = Field(ge=0, le=5)
    nota_final: float = Field(ge=0, le=5)
    comentarios: Optional[str] = None
    estado: Optional[str] = "Activo"
