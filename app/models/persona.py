from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class Persona(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    persona_id: Optional[int] = None
    documento: str = Field(min_length=3, max_length=30)
    nombres: str = Field(min_length=1, max_length=100)
    apellidos: str = Field(min_length=1, max_length=100)
    correo: str = Field(min_length=3, max_length=150)
    telefono: Optional[str] = Field(default=None, max_length=30)
    estado: str = "Activo"
