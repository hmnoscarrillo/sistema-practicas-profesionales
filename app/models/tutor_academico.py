from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TutorAcademico(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    tutor_academico_id: Optional[int] = None
    persona_id: int = Field(gt=0)
    cargo: str = Field(min_length=1, max_length=120)
    programa_id: int = Field(gt=0)
