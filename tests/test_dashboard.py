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
from mic_s3.models.alerta import Alerta, TipoAlerta, SeveridadAlerta
from mic_s3.db import set_engine
from mic_s3.services.dashboard_service import DashboardService


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
        s1 = Servicio(nombre="S1", area_id=area.id, proveedor="P1")
        s2 = Servicio(nombre="S2", area_id=area.id, proveedor="P2")
        session.add_all([s1, s2])
        session.flush()
        # Alerts
        session.add(Alerta(servicio_id=s1.id, tipo=TipoAlerta.DESVIACION_HORAS, severidad=SeveridadAlerta.MEDIA, mensaje="test", resuelta=False))
        session.add(Alerta(servicio_id=s2.id, tipo=TipoAlerta.COBERTURA_INSUFICIENTE, severidad=SeveridadAlerta.ALTA, mensaje="test2", resuelta=False))
        # Overdue proposal
        session.add(PropuestaMejora(servicio_id=s1.id, descripcion="X", responsable="Y", fecha_compromiso=date.today() - timedelta(days=5), estado=EstadoPropuesta.PENDIENTE))
        session.commit()
    yield
    set_engine(None)


def test_dashboard_kpis():
    from mic_s3.controllers.dependencies import get_session
    with get_session() as session:
        service = DashboardService(session)
        kpis = service.get_kpis(date(2026, 8, 1))
        assert kpis.total_servicios == 2
        assert kpis.alertas_activas == 2
        assert kpis.propuestas_vencidas == 1
