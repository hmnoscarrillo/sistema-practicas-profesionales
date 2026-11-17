from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Practica(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    practica_id: Optional[int] = None
    estudiante_id: int = Field(gt=0)
    empresa_id: int = Field(gt=0)
    programa_id: int = Field(gt=0)
    convenio_id: int = Field(gt=0)
    tutor_academico_id: int = Field(gt=0)
    tutor_empresarial_id: int = Field(gt=0)
    cargo: str = Field(min_length=1, max_length=150)
    fecha_inicio: date
    fecha_fin: date
    modalidad: str = Field(min_length=1, max_length=50)
    estado: Optional[str] = "En proceso"

    @model_validator(mode="after")
    def validar_fechas(self):
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("La fecha de finalización no puede ser anterior a la fecha de inicio.")
        return self
