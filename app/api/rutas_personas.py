from fastapi import APIRouter, HTTPException
from psycopg2.errors import UniqueViolation

from app.models.persona import Persona
from app.repositories.persona_repo import PersonaRepository

router = APIRouter(prefix="/personas", tags=["Personas"])
repo = PersonaRepository()


@router.get("/")
def listar_personas():
    return repo.obtener_todos()


@router.get("/{persona_id}")
def obtener_persona(persona_id: int):
    persona = repo.obtener_por_id(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada.")
    return persona


@router.post("/", status_code=201)
def crear_persona(persona: Persona):
    try:
        return {"mensaje": "Persona creada correctamente.", "persona_id": repo.crear(persona)}
    except UniqueViolation as error:
        raise HTTPException(status_code=409, detail="Ya existe una persona registrada con ese documento.") from error


@router.put("/{persona_id}")
def actualizar_persona(persona_id: int, persona: Persona):
    try:
        if not repo.actualizar(persona_id, persona):
            raise HTTPException(status_code=404, detail="Persona no encontrada.")
    except UniqueViolation as error:
        raise HTTPException(status_code=409, detail="Ya existe otra persona registrada con ese documento.") from error
    return {"mensaje": "Persona actualizada correctamente."}


@router.delete("/{persona_id}")
def eliminar_persona(persona_id: int):
    result = repo.eliminar(persona_id)
    if result == "no_encontrada":
        raise HTTPException(status_code=404, detail="Persona no encontrada.")
    return {"mensaje": "Persona eliminada correctamente."}
