from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class Estudiante(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    estudiante_id: Optional[int] = None
    documento: str = Field(min_length=1, max_length=30)
    nombres: str = Field(min_length=1, max_length=100)
    apellidos: str = Field(min_length=1, max_length=100)
    correo: str = Field(min_length=3, max_length=150)
    telefono: Optional[str] = Field(default=None, max_length=30)
    semestre: int = Field(ge=1, le=20)
    programa_id: int = Field(gt=0)
    estado: Optional[str] = "Activo"
