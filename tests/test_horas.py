import pytest
from datetime import date
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from mic_s3.models import Base
from mic_s3.models.area import Area
from mic_s3.models.servicio import Servicio
from mic_s3.models.contrato import Contrato
from mic_s3.models.ejecucion_mensual import EjecucionMensual
from mic_s3.db import set_engine
from mic_s3.services.horas_service import HorasService


@pytest.fixture(autouse=True)
def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    set_engine(engine)
    with Session(engine) as session:
        area = Area(nombre="IT", responsable="Juan")
        session.add(area)
        session.flush()
        servicio = Servicio(nombre="Servicio Alpha", area_id=area.id, proveedor="Accenture")
        session.add(servicio)
        session.flush()
        contrato = Contrato(
            servicio_id=servicio.id,
            horas_contratadas_mes=Decimal("160"),
            perfiles_contratados={"Desarrollador": 3},
            fecha_inicio=date(2026, 1, 1),
        )
        session.add(contrato)
        # Pre-existing hours
        session.add(EjecucionMensual(servicio_id=servicio.id, mes=date(2026, 6, 1), horas_reales=Decimal("150"), horas_teoricas=Decimal("160")))
        session.add(EjecucionMensual(servicio_id=servicio.id, mes=date(2026, 7, 1), horas_reales=Decimal("170"), horas_teoricas=Decimal("160")))
        session.commit()
    yield
    set_engine(None)


def test_get_horas():
    from mic_s3.controllers.dependencies import get_session
    with get_session() as session:
        service = HorasService(session)
        result = service.get_horas(1, date(2026, 6, 1), date(2026, 7, 1))
        assert result is not None
        assert len(result) == 2
        assert result[0].desviacion_pct == -6.2  # (150-160)/160 * 100
        assert result[1].desviacion_pct == 6.2   # (170-160)/160 * 100


def test_registrar_horas_new():
    from mic_s3.controllers.dependencies import get_session
    with get_session() as session:
        service = HorasService(session)
        result = service.registrar_horas(1, date(2026, 8, 1), Decimal("155"))
        assert result is not None
        assert result["horas_teoricas"] == 160.0


def test_registrar_horas_upsert():
    from mic_s3.controllers.dependencies import get_session
    with get_session() as session:
        service = HorasService(session)
        service.registrar_horas(1, date(2026, 6, 1), Decimal("145"))
        result = service.get_horas(1, date(2026, 6, 1), date(2026, 6, 1))
        assert float(result[0].horas_reales) == 145.0


def test_get_horas_not_found():
    from mic_s3.controllers.dependencies import get_session
    with get_session() as session:
        service = HorasService(session)
        assert service.get_horas(999, date(2026, 1, 1), date(2026, 12, 1)) is None
