import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from mic_s3.models import Base, Area
from mic_s3.db import set_engine
from mic_s3.services.servicio_service import ServicioService


@pytest.fixture(autouse=True)
def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    set_engine(engine)
    with Session(engine) as session:
        area = Area(nombre="IT", responsable="Juan")
        session.add(area)
        session.commit()
    yield
    set_engine(None)


def test_create_servicio():
    from mic_s3.controllers.dependencies import get_session
    with get_session() as session:
        service = ServicioService(session)
        result = service.create({
            "nombre": "Servicio Test",
            "area_id": 1,
            "proveedor": "Accenture",
        })
        assert result.id is not None
        assert result.nombre == "Servicio Test"


def test_list_servicios():
    from mic_s3.controllers.dependencies import get_session
    with get_session() as session:
        service = ServicioService(session)
        service.create({"nombre": "S1", "area_id": 1, "proveedor": "P1"})
        service.create({"nombre": "S2", "area_id": 1, "proveedor": "P2"})
        result = service.list_all()
        assert len(result) == 2


def test_get_servicio_not_found():
    from mic_s3.controllers.dependencies import get_session
    with get_session() as session:
        service = ServicioService(session)
        assert service.get_by_id(999) is None


def test_delete_servicio():
    from mic_s3.controllers.dependencies import get_session
    with get_session() as session:
        service = ServicioService(session)
        created = service.create({"nombre": "ToDelete", "area_id": 1, "proveedor": "P"})
        assert service.delete(created.id) is True
        assert service.get_by_id(created.id) is None
