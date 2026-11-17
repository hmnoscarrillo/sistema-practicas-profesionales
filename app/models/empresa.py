from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class Empresa(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    empresa_id: Optional[int] = None
    nit: str = Field(min_length=1, max_length=40)
    nombre: str = Field(min_length=1, max_length=150)
    sector: str = Field(min_length=1, max_length=100)
    ciudad: str = Field(min_length=1, max_length=100)
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    estado: Optional[str] = "Activa"
