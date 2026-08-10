from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import date
from mic_s3.controllers.dependencies import get_session
from mic_s3.services.dimensionamiento_service import DimensionamientoService

router = APIRouter(prefix="/dimensionamiento", tags=["Dimensionamiento"])


class PerfilComparacion(BaseModel):
    perfil: str
    contratados: int
    activos: int
    diferencia: int


class DimensionamientoResponse(BaseModel):
    servicio_id: int
    servicio_nombre: str
    mes: str
    perfiles: list[PerfilComparacion]
    total_contratados: int
    total_activos: int
    cobertura_pct: float


@router.get("/{servicio_id}", response_model=DimensionamientoResponse)
def get_dimensionamiento(
    servicio_id: int,
    mes: date = Query(..., description="Mes a comparar (YYYY-MM-DD, usar primer día del mes)"),
):
    """Compare contracted vs active staffing for a service in a given month."""
    with get_session() as session:
        service = DimensionamientoService(session)
        result = service.comparar(servicio_id, mes)
        if not result:
            raise HTTPException(status_code=404, detail="Servicio no encontrado")
        return DimensionamientoResponse(
            servicio_id=result.servicio_id,
            servicio_nombre=result.servicio_nombre,
            mes=result.mes,
            perfiles=[PerfilComparacion(**p) for p in result.perfiles],
            total_contratados=result.total_contratados,
            total_activos=result.total_activos,
            cobertura_pct=result.cobertura_pct,
        )
