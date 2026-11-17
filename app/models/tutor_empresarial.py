from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TutorEmpresarial(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    tutor_empresarial_id: Optional[int] = None
    persona_id: int = Field(gt=0)
    cargo: str = Field(min_length=1, max_length=120)
    empresa_id: int = Field(gt=0)
