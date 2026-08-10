import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from mic_s3.models import Base
from mic_s3.models.area import Area
from mic_s3.models.servicio import Servicio
from mic_s3.models.propuesta_mejora import PropuestaMejora, EstadoPropuesta
from mic_s3.db import set_engine
from mic_s3.services.propuestas_service import PropuestasService


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
        # One overdue proposal
        session.add(PropuestaMejora(
            servicio_id=servicio.id,
            descripcion="Mejorar tiempos",
            responsable="Ana",
            fecha_compromiso=date.today() - timedelta(days=30),
            estado=EstadoPropuesta.PENDIENTE,
        ))
        # One future proposal
        session.add(PropuestaMejora(
            servicio_id=servicio.id,
            descripcion="Actualizar docs",
            responsable="Luis",
            fecha_compromiso=date.today() + timedelta(days=30),
            estado=EstadoPropuesta.EN_CURSO,
        ))
        session.commit()
    yield
    set_engine(None)


def test_list_all():
    from mic_s3.controllers.dependencies import get_session
    with get_session() as session:
        service = PropuestasService(session)
        result = service.list_propuestas()
        assert len(result) == 2


def test_list_overdue():
    from mic_s3.controllers.dependencies import get_session
    with get_session() as session:
        service = PropuestasService(session)
        result = service.list_propuestas(overdue=True)
        assert len(result) == 1
        assert result[0].descripcion == "Mejorar tiempos"


def test_update_estado():
    from mic_s3.controllers.dependencies import get_session
    with get_session() as session:
        service = PropuestasService(session)
        result = service.update_estado(1, EstadoPropuesta.COMPLETADA)
        assert result is not None
        assert result.estado == EstadoPropuesta.COMPLETADA


def test_count_overdue():
    from mic_s3.controllers.dependencies import get_session
    with get_session() as session:
        service = PropuestasService(session)
        assert service.count_overdue() == 1


def test_create_propuesta():
    from mic_s3.controllers.dependencies import get_session
    with get_session() as session:
        service = PropuestasService(session)
        result = service.create({
            "servicio_id": 1,
            "descripcion": "Nueva propuesta",
            "responsable": "Carlos",
            "fecha_compromiso": date.today() + timedelta(days=15),
        })
        assert result.id is not None
        assert result.estado == EstadoPropuesta.PENDIENTE


def test_delete_propuesta():
    from mic_s3.controllers.dependencies import get_session
    with get_session() as session:
        service = PropuestasService(session)
        assert service.delete(1) is True
        assert service.get_by_id(1) is None
