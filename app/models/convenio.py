from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Convenio(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    convenio_id: Optional[int] = None
    codigo: str = Field(min_length=1, max_length=80)
    empresa_id: int = Field(gt=0)
    programa_id: int = Field(gt=0)
    fecha_inicio: date
    fecha_fin: date
    estado: Optional[str] = "Vigente"

    @model_validator(mode="after")
    def validar_fechas(self):
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("La fecha de finalización no puede ser anterior a la fecha de inicio.")
        return self
