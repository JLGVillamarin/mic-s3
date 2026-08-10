from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session
from mic_s3.models.servicio import Servicio
from mic_s3.models.contrato import Contrato
from mic_s3.models.colaborador_bran import ColaboradorBran
from mic_s3.models.ejecucion_mensual import EjecucionMensual
from mic_s3.models.propuesta_mejora import PropuestaMejora, EstadoPropuesta
from mic_s3.models.alerta import Alerta, TipoAlerta, SeveridadAlerta

# Thresholds (business rules)
HORAS_DESVIACION_WARNING_PCT = 10  # RB-01: >10% deviation
HORAS_DESVIACION_CRITICAL_PCT = 20  # RB-02: >20% critical
COBERTURA_WARNING_PCT = 80  # RB-03: <80% coverage
COBERTURA_CRITICAL_PCT = 60  # RB-04: <60% critical
CONTRATO_VENCER_DIAS = 90  # RB-05: contract expiring within 90 days
PROPUESTA_VENCIDA_DIAS = 0  # RB-06: overdue proposals


class AlertasEngine:
    def __init__(self, session: Session):
        self.session = session

    def run_all(self, mes: date | None = None) -> list[Alerta]:
        """Run all alert rules and create new alerts. Returns newly created alerts."""
        if mes is None:
            mes = date.today().replace(day=1)

        new_alerts = []
        servicios = list(self.session.scalars(select(Servicio)))

        for servicio in servicios:
            new_alerts.extend(self._check_horas(servicio, mes))
            new_alerts.extend(self._check_cobertura(servicio, mes))
            new_alerts.extend(self._check_contrato_vencimiento(servicio))
            new_alerts.extend(self._check_propuestas_vencidas(servicio))

        self.session.commit()
        return new_alerts

    def _create_alert(self, servicio_id: int, tipo: TipoAlerta, severidad: SeveridadAlerta, mensaje: str) -> Alerta:
        # Check if similar unresolved alert already exists
        existing = self.session.scalars(
            select(Alerta).where(
                and_(
                    Alerta.servicio_id == servicio_id,
                    Alerta.tipo == tipo,
                    Alerta.resuelta == False,
                )
            )
        ).first()
        if existing:
            existing.mensaje = mensaje
            return existing

        alerta = Alerta(
            servicio_id=servicio_id,
            tipo=tipo,
            severidad=severidad,
            mensaje=mensaje,
        )
        self.session.add(alerta)
        return alerta

    def _check_horas(self, servicio: Servicio, mes: date) -> list[Alerta]:
        alerts = []
        ejecucion = self.session.scalars(
            select(EjecucionMensual).where(
                and_(
                    EjecucionMensual.servicio_id == servicio.id,
                    EjecucionMensual.mes == mes,
                )
            )
        ).first()
        if not ejecucion or ejecucion.horas_teoricas == 0:
            return alerts

        desviacion_pct = abs(float((ejecucion.horas_reales - ejecucion.horas_teoricas) / ejecucion.horas_teoricas) * 100)

        if desviacion_pct >= HORAS_DESVIACION_CRITICAL_PCT:
            alerts.append(self._create_alert(
                servicio.id, TipoAlerta.DESVIACION_HORAS, SeveridadAlerta.CRITICA,
                f"Desviación de horas crítica: {desviacion_pct:.1f}% en {mes.isoformat()}"
            ))
        elif desviacion_pct >= HORAS_DESVIACION_WARNING_PCT:
            alerts.append(self._create_alert(
                servicio.id, TipoAlerta.DESVIACION_HORAS, SeveridadAlerta.MEDIA,
                f"Desviación de horas: {desviacion_pct:.1f}% en {mes.isoformat()}"
            ))
        return alerts

    def _check_cobertura(self, servicio: Servicio, mes: date) -> list[Alerta]:
        alerts = []
        contrato = self.session.scalars(
            select(Contrato).where(Contrato.servicio_id == servicio.id)
        ).first()
        if not contrato or not contrato.perfiles_contratados:
            return alerts

        total_contratados = sum(int(v) for v in contrato.perfiles_contratados.values())
        if total_contratados == 0:
            return alerts

        total_activos = self.session.scalar(
            select(func.count()).where(
                and_(
                    ColaboradorBran.servicio_id == servicio.id,
                    ColaboradorBran.mes == mes,
                    ColaboradorBran.activo == True,
                )
            )
        ) or 0

        cobertura_pct = (total_activos / total_contratados) * 100

        if cobertura_pct < COBERTURA_CRITICAL_PCT:
            alerts.append(self._create_alert(
                servicio.id, TipoAlerta.COBERTURA_INSUFICIENTE, SeveridadAlerta.ALTA,
                f"Cobertura crítica: {cobertura_pct:.0f}% ({total_activos}/{total_contratados}) en {mes.isoformat()}"
            ))
        elif cobertura_pct < COBERTURA_WARNING_PCT:
            alerts.append(self._create_alert(
                servicio.id, TipoAlerta.COBERTURA_INSUFICIENTE, SeveridadAlerta.MEDIA,
                f"Cobertura insuficiente: {cobertura_pct:.0f}% ({total_activos}/{total_contratados}) en {mes.isoformat()}"
            ))
        return alerts

    def _check_contrato_vencimiento(self, servicio: Servicio) -> list[Alerta]:
        alerts = []
        contrato = self.session.scalars(
            select(Contrato).where(Contrato.servicio_id == servicio.id)
        ).first()
        if not contrato or not contrato.fecha_fin:
            return alerts

        dias_restantes = (contrato.fecha_fin - date.today()).days
        if dias_restantes <= CONTRATO_VENCER_DIAS and dias_restantes >= 0:
            severidad = SeveridadAlerta.ALTA if dias_restantes <= 30 else SeveridadAlerta.MEDIA
            alerts.append(self._create_alert(
                servicio.id, TipoAlerta.CONTRATO_PROXIMO_VENCER, severidad,
                f"Contrato vence en {dias_restantes} días ({contrato.fecha_fin.isoformat()})"
            ))
        return alerts

    def _check_propuestas_vencidas(self, servicio: Servicio) -> list[Alerta]:
        alerts = []
        count = self.session.scalar(
            select(func.count()).where(
                and_(
                    PropuestaMejora.servicio_id == servicio.id,
                    PropuestaMejora.fecha_compromiso < date.today(),
                    PropuestaMejora.estado.notin_([EstadoPropuesta.COMPLETADA, EstadoPropuesta.CANCELADA]),
                )
            )
        ) or 0

        if count > 0:
            severidad = SeveridadAlerta.ALTA if count >= 3 else SeveridadAlerta.MEDIA
            alerts.append(self._create_alert(
                servicio.id, TipoAlerta.PROPUESTA_VENCIDA, severidad,
                f"{count} propuesta(s) de mejora vencida(s)"
            ))
        return alerts
