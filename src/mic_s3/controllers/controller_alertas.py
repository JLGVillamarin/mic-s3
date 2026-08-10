from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import date, datetime
from mic_s3.models.alerta import TipoAlerta, SeveridadAlerta
from mic_s3.controllers.dependencies import get_session
from mic_s3.services.alertas_engine import AlertasEngine
from sqlalchemy import select, and_
from mic_s3.models.alerta import Alerta

router = APIRouter(prefix="/alertas", tags=["Alertas"])


class AlertaResponse(BaseModel):
    id: int
    servicio_id: int
    tipo: TipoAlerta
    severidad: SeveridadAlerta
    mensaje: str
    fecha_generacion: datetime | None
    resuelta: bool

    class Config:
        from_attributes = True


class RunAlertasResponse(BaseModel):
    new_alerts: int
    total_active: int


@router.get("/", response_model=list[AlertaResponse])
def list_alertas(
    servicio_id: int | None = Query(None),
    resuelta: bool | None = Query(None),
):
    with get_session() as session:
        stmt = select(Alerta)
        conditions = []
        if servicio_id:
            conditions.append(Alerta.servicio_id == servicio_id)
        if resuelta is not None:
            conditions.append(Alerta.resuelta == resuelta)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(Alerta.fecha_generacion.desc())
        return list(session.scalars(stmt))


@router.patch("/{alerta_id}/resolver", response_model=AlertaResponse)
def resolver_alerta(alerta_id: int):
    with get_session() as session:
        alerta = session.get(Alerta, alerta_id)
        if not alerta:
            raise HTTPException(status_code=404, detail="Alerta no encontrada")
        alerta.resuelta = True
        session.commit()
        session.refresh(alerta)
        return alerta


@router.post("/run", response_model=RunAlertasResponse)
def run_alertas(mes: date | None = Query(None, description="Mes para evaluar (YYYY-MM-DD)")):
    """Trigger alert engine to evaluate all rules."""
    with get_session() as session:
        engine = AlertasEngine(session)
        new_alerts = engine.run_all(mes)
        total_active = len(list(session.scalars(
            select(Alerta).where(Alerta.resuelta == False)
        )))
        return RunAlertasResponse(new_alerts=len(new_alerts), total_active=total_active)
