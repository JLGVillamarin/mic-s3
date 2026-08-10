from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import date, datetime
from mic_s3.models.propuesta_mejora import EstadoPropuesta
from mic_s3.controllers.dependencies import get_session
from mic_s3.services.propuestas_service import PropuestasService

router = APIRouter(prefix="/propuestas", tags=["Propuestas de Mejora"])


class PropuestaCreateRequest(BaseModel):
    servicio_id: int
    acta_id: int | None = None
    descripcion: str
    responsable: str
    fecha_compromiso: date
    estado: EstadoPropuesta = EstadoPropuesta.PENDIENTE


class PropuestaUpdateRequest(BaseModel):
    descripcion: str | None = None
    responsable: str | None = None
    fecha_compromiso: date | None = None
    estado: EstadoPropuesta | None = None


class PropuestaEstadoRequest(BaseModel):
    estado: EstadoPropuesta


class PropuestaResponse(BaseModel):
    id: int
    servicio_id: int
    acta_id: int | None
    descripcion: str
    responsable: str
    fecha_compromiso: date
    estado: EstadoPropuesta
    created_at: datetime | None

    class Config:
        from_attributes = True


@router.get("/", response_model=list[PropuestaResponse])
def list_propuestas(
    servicio_id: int | None = Query(None),
    estado: EstadoPropuesta | None = Query(None),
    overdue: bool = Query(False, description="Filtrar solo propuestas vencidas"),
):
    with get_session() as session:
        service = PropuestasService(session)
        return service.list_propuestas(servicio_id=servicio_id, estado=estado, overdue=overdue)


@router.get("/{propuesta_id}", response_model=PropuestaResponse)
def get_propuesta(propuesta_id: int):
    with get_session() as session:
        service = PropuestasService(session)
        propuesta = service.get_by_id(propuesta_id)
        if not propuesta:
            raise HTTPException(status_code=404, detail="Propuesta no encontrada")
        return propuesta


@router.post("/", response_model=PropuestaResponse, status_code=201)
def create_propuesta(request: PropuestaCreateRequest):
    with get_session() as session:
        service = PropuestasService(session)
        return service.create(request.model_dump())


@router.put("/{propuesta_id}", response_model=PropuestaResponse)
def update_propuesta(propuesta_id: int, request: PropuestaUpdateRequest):
    with get_session() as session:
        service = PropuestasService(session)
        data = request.model_dump(exclude_none=True)
        result = service.update(propuesta_id, data)
        if not result:
            raise HTTPException(status_code=404, detail="Propuesta no encontrada")
        return result


@router.patch("/{propuesta_id}/estado", response_model=PropuestaResponse)
def update_propuesta_estado(propuesta_id: int, request: PropuestaEstadoRequest):
    with get_session() as session:
        service = PropuestasService(session)
        result = service.update_estado(propuesta_id, request.estado)
        if not result:
            raise HTTPException(status_code=404, detail="Propuesta no encontrada")
        return result


@router.delete("/{propuesta_id}", status_code=204)
def delete_propuesta(propuesta_id: int):
    with get_session() as session:
        service = PropuestasService(session)
        if not service.delete(propuesta_id):
            raise HTTPException(status_code=404, detail="Propuesta no encontrada")
