from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import date
from decimal import Decimal
from mic_s3.controllers.dependencies import get_session
from mic_s3.services.horas_service import HorasService

router = APIRouter(prefix="/horas", tags=["Horas"])


class HorasMesResponse(BaseModel):
    mes: date
    horas_reales: float
    horas_teoricas: float
    desviacion: float
    desviacion_pct: float


class HorasListResponse(BaseModel):
    servicio_id: int
    registros: list[HorasMesResponse]


class HorasRegistrarRequest(BaseModel):
    servicio_id: int
    mes: date
    horas_reales: Decimal


class HorasRegistrarResponse(BaseModel):
    servicio_id: int
    mes: str
    horas_reales: float
    horas_teoricas: float


@router.get("/{servicio_id}", response_model=HorasListResponse)
def get_horas(
    servicio_id: int,
    desde: date = Query(..., description="Fecha inicio (YYYY-MM-DD)"),
    hasta: date = Query(..., description="Fecha fin (YYYY-MM-DD)"),
):
    """Get monthly hours tracking for a service."""
    with get_session() as session:
        service = HorasService(session)
        result = service.get_horas(servicio_id, desde, hasta)
        if result is None:
            raise HTTPException(status_code=404, detail="Servicio no encontrado")
        return HorasListResponse(
            servicio_id=servicio_id,
            registros=[
                HorasMesResponse(
                    mes=r.mes,
                    horas_reales=float(r.horas_reales),
                    horas_teoricas=float(r.horas_teoricas),
                    desviacion=float(r.desviacion),
                    desviacion_pct=r.desviacion_pct,
                )
                for r in result
            ],
        )


@router.post("/", response_model=HorasRegistrarResponse, status_code=201)
def registrar_horas(request: HorasRegistrarRequest):
    """Register real hours for a service in a given month."""
    with get_session() as session:
        service = HorasService(session)
        result = service.registrar_horas(request.servicio_id, request.mes, request.horas_reales)
        if result is None:
            raise HTTPException(status_code=404, detail="Servicio no encontrado")
        return HorasRegistrarResponse(**result)
