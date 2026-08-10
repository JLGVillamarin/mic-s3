from datetime import date
from decimal import Decimal
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
from mic_s3.models.servicio import Servicio
from mic_s3.models.alerta import Alerta
from mic_s3.models.propuesta_mejora import PropuestaMejora, EstadoPropuesta
from mic_s3.models.ejecucion_mensual import EjecucionMensual
from mic_s3.models.contrato import Contrato
from mic_s3.models.colaborador_bran import ColaboradorBran
from mic_s3.models.acta import Acta


class DashboardKPIs:
    def __init__(self):
        self.total_servicios: int = 0
        self.alertas_activas: int = 0
        self.propuestas_vencidas: int = 0
        self.desviacion_media_horas_pct: float = 0.0
        self.cobertura_media_pct: float = 0.0
        self.actas_ultimo_mes: int = 0


class DashboardService:
    def __init__(self, session: Session):
        self.session = session

    def get_kpis(self, mes: date | None = None) -> DashboardKPIs:
        if mes is None:
            mes = date.today().replace(day=1)

        kpis = DashboardKPIs()

        # Total servicios
        kpis.total_servicios = self.session.scalar(select(func.count()).select_from(Servicio)) or 0

        # Alertas activas
        kpis.alertas_activas = self.session.scalar(
            select(func.count()).where(Alerta.resuelta == False)
        ) or 0

        # Propuestas vencidas
        kpis.propuestas_vencidas = self.session.scalar(
            select(func.count()).where(
                and_(
                    PropuestaMejora.fecha_compromiso < date.today(),
                    PropuestaMejora.estado.notin_([EstadoPropuesta.COMPLETADA, EstadoPropuesta.CANCELADA]),
                )
            )
        ) or 0

        # Desviación media de horas (for current month)
        ejecuciones = list(self.session.scalars(
            select(EjecucionMensual).where(EjecucionMensual.mes == mes)
        ))
        if ejecuciones:
            desviaciones = []
            for e in ejecuciones:
                if e.horas_teoricas > 0:
                    desviaciones.append(
                        abs(float((e.horas_reales - e.horas_teoricas) / e.horas_teoricas) * 100)
                    )
            kpis.desviacion_media_horas_pct = round(sum(desviaciones) / len(desviaciones), 1) if desviaciones else 0.0

        # Cobertura media
        servicios_con_contrato = list(self.session.scalars(select(Contrato)))
        coberturas = []
        for contrato in servicios_con_contrato:
            if not contrato.perfiles_contratados:
                continue
            total_contratados = sum(int(v) for v in contrato.perfiles_contratados.values())
            if total_contratados == 0:
                continue
            total_activos = self.session.scalar(
                select(func.count()).where(
                    and_(
                        ColaboradorBran.servicio_id == contrato.servicio_id,
                        ColaboradorBran.mes == mes,
                        ColaboradorBran.activo == True,
                    )
                )
            ) or 0
            coberturas.append((total_activos / total_contratados) * 100)
        kpis.cobertura_media_pct = round(sum(coberturas) / len(coberturas), 1) if coberturas else 100.0

        # Actas último mes
        kpis.actas_ultimo_mes = self.session.scalar(
            select(func.count()).where(
                and_(
                    Acta.fecha_reunion >= mes,
                    Acta.fecha_reunion < mes.replace(month=mes.month + 1) if mes.month < 12 else mes.replace(year=mes.year + 1, month=1),
                )
            )
        ) or 0

        return kpis
