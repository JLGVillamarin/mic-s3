from fastapi import APIRouter, Query
from pydantic import BaseModel
from datetime import date
from mic_s3.controllers.dependencies import get_session
from mic_s3.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


class DashboardResponse(BaseModel):
    total_servicios: int
    alertas_activas: int
    propuestas_vencidas: int
    desviacion_media_horas_pct: float
    cobertura_media_pct: float
    actas_ultimo_mes: int


@router.get("/", response_model=DashboardResponse)
def get_dashboard(mes: date | None = Query(None, description="Mes de referencia (YYYY-MM-DD)")):
    """Get dashboard KPIs."""
    with get_session() as session:
        service = DashboardService(session)
        kpis = service.get_kpis(mes)
        return DashboardResponse(
            total_servicios=kpis.total_servicios,
            alertas_activas=kpis.alertas_activas,
            propuestas_vencidas=kpis.propuestas_vencidas,
            desviacion_media_horas_pct=kpis.desviacion_media_horas_pct,
            cobertura_media_pct=kpis.cobertura_media_pct,
            actas_ultimo_mes=kpis.actas_ultimo_mes,
        )
