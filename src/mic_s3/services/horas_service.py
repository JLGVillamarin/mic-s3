from datetime import date
from decimal import Decimal
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from mic_s3.models.servicio import Servicio
from mic_s3.models.contrato import Contrato
from mic_s3.models.ejecucion_mensual import EjecucionMensual


class HorasMesResult:
    def __init__(self, mes: date, horas_reales: Decimal, horas_teoricas: Decimal):
        self.mes = mes
        self.horas_reales = horas_reales
        self.horas_teoricas = horas_teoricas
        self.desviacion = horas_reales - horas_teoricas
        self.desviacion_pct = (
            round(float((horas_reales - horas_teoricas) / horas_teoricas) * 100, 1)
            if horas_teoricas > 0 else 0.0
        )


class HorasService:
    def __init__(self, session: Session):
        self.session = session

    def get_horas(self, servicio_id: int, desde: date, hasta: date) -> list[HorasMesResult] | None:
        """Get monthly hours comparison for a service in a date range."""
        servicio = self.session.get(Servicio, servicio_id)
        if not servicio:
            return None

        ejecuciones = list(self.session.scalars(
            select(EjecucionMensual).where(
                and_(
                    EjecucionMensual.servicio_id == servicio_id,
                    EjecucionMensual.mes >= desde,
                    EjecucionMensual.mes <= hasta,
                )
            ).order_by(EjecucionMensual.mes)
        ))

        return [
            HorasMesResult(
                mes=e.mes,
                horas_reales=e.horas_reales,
                horas_teoricas=e.horas_teoricas,
            )
            for e in ejecuciones
        ]

    def registrar_horas(self, servicio_id: int, mes: date, horas_reales: Decimal) -> dict | None:
        """Register real hours for a month. Theoretical is auto-calculated from contract."""
        servicio = self.session.get(Servicio, servicio_id)
        if not servicio:
            return None

        # Get theoretical from contract
        contrato = self.session.scalars(
            select(Contrato).where(Contrato.servicio_id == servicio_id)
        ).first()
        horas_teoricas = contrato.horas_contratadas_mes if contrato else Decimal("0")

        # Upsert
        existing = self.session.scalars(
            select(EjecucionMensual).where(
                and_(
                    EjecucionMensual.servicio_id == servicio_id,
                    EjecucionMensual.mes == mes,
                )
            )
        ).first()

        if existing:
            existing.horas_reales = horas_reales
            existing.horas_teoricas = horas_teoricas
        else:
            ejecucion = EjecucionMensual(
                servicio_id=servicio_id,
                mes=mes,
                horas_reales=horas_reales,
                horas_teoricas=horas_teoricas,
            )
            self.session.add(ejecucion)

        self.session.commit()
        return {"servicio_id": servicio_id, "mes": mes.isoformat(), "horas_reales": float(horas_reales), "horas_teoricas": float(horas_teoricas)}
