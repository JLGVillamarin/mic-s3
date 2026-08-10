import pytest
from io import BytesIO
from openpyxl import Workbook
from sqlalchemy import create_engine, select, and_
from sqlalchemy.orm import Session
from datetime import date
from mic_s3.models import Base, Area
from mic_s3.models.servicio import Servicio
from mic_s3.models.colaborador_bran import ColaboradorBran
from mic_s3.db import set_engine
from mic_s3.parsers.bran_parser import parse_bran_excel, BranParserError
from mic_s3.services.bran_import_service import BranImportService


def _make_excel(rows: list[list]) -> bytes:
    """Helper to create Excel bytes from rows (first row is header)."""
    wb = Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


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
        session.commit()
    yield
    set_engine(None)


def test_parse_valid_excel():
    content = _make_excel([
        ["Nombre", "Perfil", "Servicio"],
        ["Ana García", "Desarrollador", "Servicio Alpha"],
        ["Luis López", "Analista", "Servicio Alpha"],
    ])
    rows = parse_bran_excel(content)
    assert len(rows) == 2
    assert rows[0].nombre == "Ana García"


def test_parse_missing_columns():
    content = _make_excel([["Nombre", "Cargo"]])
    with pytest.raises(BranParserError, match="Columnas requeridas"):
        parse_bran_excel(content)


def test_parse_empty_file():
    content = _make_excel([["Nombre", "Perfil", "Servicio"]])
    with pytest.raises(BranParserError, match="vacío"):
        parse_bran_excel(content)


def test_preview_warns_unknown_servicio():
    content = _make_excel([
        ["Nombre", "Perfil", "Servicio"],
        ["Ana", "Dev", "Servicio Desconocido"],
    ])
    from mic_s3.controllers.dependencies import get_session
    with get_session() as session:
        service = BranImportService(session)
        result = service.preview(content)
        assert "Servicio Desconocido" in result.servicios_not_found


def test_confirm_creates_snapshot():
    content = _make_excel([
        ["Nombre", "Perfil", "Servicio"],
        ["Ana García", "Dev", "Servicio Alpha"],
        ["Luis López", "QA", "Servicio Alpha"],
    ])
    from mic_s3.controllers.dependencies import get_session
    with get_session() as session:
        service = BranImportService(session)
        result = service.confirm(content, date(2026, 8, 1))
        assert result["created"] == 2
        assert result["skipped"] == 0


def test_confirm_marks_inactive():
    content1 = _make_excel([
        ["Nombre", "Perfil", "Servicio"],
        ["Ana", "Dev", "Servicio Alpha"],
        ["Luis", "QA", "Servicio Alpha"],
    ])
    content2 = _make_excel([
        ["Nombre", "Perfil", "Servicio"],
        ["Ana", "Dev", "Servicio Alpha"],
    ])
    from mic_s3.controllers.dependencies import get_session
    mes = date(2026, 8, 1)
    with get_session() as session:
        service = BranImportService(session)
        service.confirm(content1, mes)
        service.confirm(content2, mes)
        # Luis should be inactive
        luis = session.scalars(
            select(ColaboradorBran).where(
                and_(ColaboradorBran.nombre == "Luis", ColaboradorBran.mes == mes)
            )
        ).first()
        assert luis is not None
        assert luis.activo is False
