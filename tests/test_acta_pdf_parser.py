from io import BytesIO

import pytest

from mic_s3.parsers.acta_parser_errors import ActaExtractionError, ActaFormatError
from mic_s3.parsers.acta_pdf_parser import parse_acta_pdf


def _make_pdf(text: str) -> bytes:
    """Create a simple PDF with text content using fpdf2."""
    try:
        from fpdf import FPDF
    except ImportError:
        pytest.skip("fpdf2 not installed")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    for line in text.split("\n"):
        pdf.cell(0, 8, text=line, new_x="LMARGIN", new_y="NEXT")
    buffer = BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()


def test_parse_single_service_acta():
    text = """Acta de Seguimiento
Fecha: 15/08/2026
Servicio: Servicio Alpha
Asistentes: Juan Perez, Maria Lopez
Revision del estado del servicio y metricas mensuales.
Propuestas de Mejora
- Mejorar tiempos de respuesta - Responsable: Juan - Fecha: 30/09/2026
- Actualizar documentacion"""
    result = parse_acta_pdf(_make_pdf(text))
    assert len(result.services) == 1
    svc = result.services[0]
    assert svc.servicio_nombre == "Servicio Alpha"
    assert svc.fecha_reunion == "2026-08-15"
    assert len(svc.asistentes) == 2
    assert len(svc.propuestas) >= 1


def test_parse_multi_service_acta():
    text = """Acta de Seguimiento Mensual
Fecha: 10/08/2026
Servicio: Servicio Alpha
Asistentes: Ana
Todo correcto en Alpha.
Propuestas de Mejora
- Migrar a nueva version
Servicio: Servicio Beta
Asistentes: Luis, Pedro
Pendiente revision Beta.
Propuestas de Mejora
- Contratar perfil adicional - Responsable: Luis - Fecha: 15/09/2026"""
    result = parse_acta_pdf(_make_pdf(text))
    assert len(result.services) == 2
    assert result.services[0].servicio_nombre == "Servicio Alpha"
    assert result.services[1].servicio_nombre == "Servicio Beta"


def test_parse_empty_pdf():
    try:
        from fpdf import FPDF
    except ImportError:
        pytest.skip("fpdf2 not installed")
    pdf = FPDF()
    pdf.add_page()
    buffer = BytesIO()
    pdf.output(buffer)
    with pytest.raises(ActaFormatError, match="No se pudo extraer texto"):
        parse_acta_pdf(buffer.getvalue())


def test_parse_invalid_bytes():
    with pytest.raises(ActaFormatError, match="No se pudo abrir"):
        parse_acta_pdf(b"not a pdf")


def test_parse_no_service_marker():
    text = """Acta de Reunion
Fecha: 01/07/2026
Asistentes: Carlos
Discusion general sobre el proyecto."""
    result = parse_acta_pdf(_make_pdf(text))
    assert len(result.services) == 1
    assert result.services[0].servicio_nombre == "(sin identificar)"
    assert any("sin identificar" in w.lower() or "marcador" in w.lower() for w in result.warnings)
