import pytest
from datetime import date
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from mic_s3.models import Base
from mic_s3.models.area import Area
from mic_s3.models.servicio import Servicio
from mic_s3.models.contrato import Contrato
from mic_s3.models.colaborador_bran import ColaboradorBran
from mic_s3.db import set_engine
from mic_s3.services.dimensionamiento_service import DimensionamientoService


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
            perfiles_contratados={"Desarrollador": 3, "Analista": 1},
            fecha_inicio=date(2026, 1, 1),
        )
        session.add(contrato)
        # Add BRAN collaborators for Aug 2026
        mes = date(2026, 8, 1)
        for nombre in ["Ana", "Luis"]:
            session.add(ColaboradorBran(servicio_id=servicio.id, nombre=nombre, perfil="Desarrollador", mes=mes, activo=True))
        session.add(ColaboradorBran(servicio_id=servicio.id, nombre="Carlos", perfil="Analista", mes=mes, activo=True))
        session.commit()
    yield
    set_engine(None)


def test_comparar_basic():
    from mic_s3.controllers.dependencies import get_session
    with get_session() as session:
        service = DimensionamientoService(session)
        result = service.comparar(1, date(2026, 8, 1))
        assert result is not None
        assert result.total_contratados == 4
        assert result.total_activos == 3
        # Desarrollador: 3 contracted, 2 active => -1
        dev = next(p for p in result.perfiles if p["perfil"] == "Desarrollador")
        assert dev["contratados"] == 3
        assert dev["activos"] == 2
        assert dev["diferencia"] == -1


def test_comparar_full_coverage():
    from mic_s3.controllers.dependencies import get_session
    with get_session() as session:
        # Analista: 1 contracted, 1 active => 0
        service = DimensionamientoService(session)
        result = service.comparar(1, date(2026, 8, 1))
        analista = next(p for p in result.perfiles if p["perfil"] == "Analista")
        assert analista["diferencia"] == 0


def test_comparar_not_found():
    from mic_s3.controllers.dependencies import get_session
    with get_session() as session:
        service = DimensionamientoService(session)
        assert service.comparar(999, date(2026, 8, 1)) is None


def test_cobertura_percentage():
    from mic_s3.controllers.dependencies import get_session
    with get_session() as session:
        service = DimensionamientoService(session)
        result = service.comparar(1, date(2026, 8, 1))
        # 3 activos / 4 contratados = 75%
        assert result.cobertura_pct == 75.0
