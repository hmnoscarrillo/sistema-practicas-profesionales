from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class Programa(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    programa_id: Optional[int] = None
    nombre: str = Field(min_length=1, max_length=150)
    facultad: str = Field(min_length=1, max_length=150)
    nivel: str = Field(min_length=1, max_length=60)
    duracion_semestres: int = Field(ge=1, le=20)
    estado: Optional[str] = "Activo"
