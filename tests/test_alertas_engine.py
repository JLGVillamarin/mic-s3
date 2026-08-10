import pytest
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from mic_s3.models import Base
from mic_s3.models.area import Area
from mic_s3.models.servicio import Servicio
from mic_s3.models.contrato import Contrato
from mic_s3.models.colaborador_bran import ColaboradorBran
from mic_s3.models.ejecucion_mensual import EjecucionMensual
from mic_s3.models.propuesta_mejora import PropuestaMejora, EstadoPropuesta
from mic_s3.models.alerta import Alerta, TipoAlerta
from mic_s3.db import set_engine
from mic_s3.services.alertas_engine import AlertasEngine


@pytest.fixture(autouse=True)
def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    set_engine(engine)
    mes = date(2026, 8, 1)
    with Session(engine) as session:
        area = Area(nombre="IT", responsable="Juan")
        session.add(area)
        session.flush()
        servicio = Servicio(nombre="Servicio Alpha", area_id=area.id, proveedor="Accenture")
        session.add(servicio)
        session.flush()
        # Contract with 4 profiles
        contrato = Contrato(
            servicio_id=servicio.id,
            horas_contratadas_mes=Decimal("160"),
            perfiles_contratados={"Dev": 3, "QA": 1},
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date.today() + timedelta(days=60),  # expires in 60 days
        )
        session.add(contrato)
        # Only 2 active BRAN (50% coverage - critical)
        session.add(ColaboradorBran(servicio_id=servicio.id, nombre="Ana", perfil="Dev", mes=mes, activo=True))
        session.add(ColaboradorBran(servicio_id=servicio.id, nombre="Luis", perfil="Dev", mes=mes, activo=True))
        # Hours with 25% deviation (critical)
        session.add(EjecucionMensual(servicio_id=servicio.id, mes=mes, horas_reales=Decimal("200"), horas_teoricas=Decimal("160")))
        # Overdue proposal
        session.add(PropuestaMejora(
            servicio_id=servicio.id, descripcion="Test", responsable="X",
            fecha_compromiso=date.today() - timedelta(days=10), estado=EstadoPropuesta.PENDIENTE,
        ))
        session.commit()
    yield
    set_engine(None)


def test_run_all_generates_alerts():
    from mic_s3.controllers.dependencies import get_session
    with get_session() as session:
        engine = AlertasEngine(session)
        alerts = engine.run_all(date(2026, 8, 1))
        assert len(alerts) >= 3  # horas, cobertura, contrato or propuesta
        tipos = {a.tipo for a in alerts}
        assert TipoAlerta.DESVIACION_HORAS in tipos
        assert TipoAlerta.COBERTURA_INSUFICIENTE in tipos


def test_horas_critical():
    from mic_s3.controllers.dependencies import get_session
    with get_session() as session:
        engine = AlertasEngine(session)
        alerts = engine.run_all(date(2026, 8, 1))
        horas_alert = next(a for a in alerts if a.tipo == TipoAlerta.DESVIACION_HORAS)
        assert "crítica" in horas_alert.mensaje.lower() or "25" in horas_alert.mensaje


def test_no_duplicate_alerts():
    from mic_s3.controllers.dependencies import get_session
    with get_session() as session:
        engine = AlertasEngine(session)
        engine.run_all(date(2026, 8, 1))
        engine.run_all(date(2026, 8, 1))
        # Should not duplicate - same alert updated
        from sqlalchemy import select, func
        count = session.scalar(select(func.count()).select_from(Alerta))
        assert count <= 4  # max 4 types of alerts


def test_contrato_vencimiento_alert():
    from mic_s3.controllers.dependencies import get_session
    with get_session() as session:
        engine = AlertasEngine(session)
        alerts = engine.run_all(date(2026, 8, 1))
        contrato_alerts = [a for a in alerts if a.tipo == TipoAlerta.CONTRATO_PROXIMO_VENCER]
        assert len(contrato_alerts) == 1
