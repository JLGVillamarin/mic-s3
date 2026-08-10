from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import date
from decimal import Decimal
from mic_s3.models.servicio import EstadoServicio
from mic_s3.services.servicio_service import ServicioService
from mic_s3.controllers.dependencies import get_session

router = APIRouter(prefix="/servicios", tags=["Servicios"])

# --- Schemas ---


class ContratoSchema(BaseModel):
    horas_contratadas_mes: Decimal
    perfiles_contratados: dict = Field(default_factory=dict)
    fecha_inicio: date
    fecha_fin: date | None = None


class ServicioCreateRequest(BaseModel):
    nombre: str
    area_id: int
    proveedor: str
    estado: EstadoServicio = EstadoServicio.ACTIVO
    contrato: ContratoSchema | None = None


class ServicioUpdateRequest(BaseModel):
    nombre: str | None = None
    area_id: int | None = None
    proveedor: str | None = None
    estado: EstadoServicio | None = None
    contrato: ContratoSchema | None = None


class ContratoResponse(BaseModel):
    id: int
    horas_contratadas_mes: Decimal
    perfiles_contratados: dict
    fecha_inicio: date
    fecha_fin: date | None

    class Config:
        from_attributes = True


class ServicioResponse(BaseModel):
    id: int
    nombre: str
    area_id: int
    proveedor: str
    estado: EstadoServicio
    contrato: ContratoResponse | None = None

    class Config:
        from_attributes = True


# --- Endpoints ---


@router.get("/", response_model=list[ServicioResponse])
def list_servicios():
    with get_session() as session:
        service = ServicioService(session)
        return service.list_all()


@router.get("/{servicio_id}", response_model=ServicioResponse)
def get_servicio(servicio_id: int):
    with get_session() as session:
        service = ServicioService(session)
        servicio = service.get_by_id(servicio_id)
        if not servicio:
            raise HTTPException(status_code=404, detail="Servicio no encontrado")
        return servicio


@router.post("/", response_model=ServicioResponse, status_code=201)
def create_servicio(request: ServicioCreateRequest):
    with get_session() as session:
        service = ServicioService(session)
        data = request.model_dump(exclude_none=True)
        if data.get("contrato"):
            data["contrato"] = request.contrato.model_dump()
        return service.create(data)


@router.put("/{servicio_id}", response_model=ServicioResponse)
def update_servicio(servicio_id: int, request: ServicioUpdateRequest):
    with get_session() as session:
        service = ServicioService(session)
        data = request.model_dump(exclude_none=True)
        if request.contrato:
            data["contrato"] = request.contrato.model_dump()
        result = service.update(servicio_id, data)
        if not result:
            raise HTTPException(status_code=404, detail="Servicio no encontrado")
        return result


@router.delete("/{servicio_id}", status_code=204)
def delete_servicio(servicio_id: int):
    with get_session() as session:
        service = ServicioService(session)
        if not service.delete(servicio_id):
            raise HTTPException(status_code=404, detail="Servicio no encontrado")
