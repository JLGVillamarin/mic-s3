import re
from dataclasses import dataclass, field
from io import BytesIO

import pdfplumber

from mic_s3.parsers.acta_parser_errors import ActaExtractionError, ActaFormatError


@dataclass
class ActaParsedService:
    """Data extracted for one service from an acta."""
    servicio_nombre: str
    fecha_reunion: str  # YYYY-MM-DD string, to be validated later
    asistentes: list[str] = field(default_factory=list)
    puntos_tratados: str = ""
    propuestas: list[dict] = field(default_factory=list)  # [{descripcion, responsable, fecha_compromiso}]


@dataclass
class ActaParsedResult:
    services: list[ActaParsedService]
    raw_text: str
    warnings: list[str] = field(default_factory=list)


# Common section header patterns (case-insensitive)
_DATE_PATTERN = re.compile(r"fecha[:\s]*(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})", re.IGNORECASE)
_SERVICE_PATTERN = re.compile(r"servicio[:\s]*(.+)", re.IGNORECASE)
_ATTENDEES_PATTERN = re.compile(r"asistentes[:\s]*(.*)", re.IGNORECASE)
_PROPOSALS_HEADER = re.compile(r"propuestas?\s*(de\s*)?mejora", re.IGNORECASE)
_PROPOSAL_ROW = re.compile(
    r"[-\u2022]\s*(.+?)(?:\s*[-\u2013|]\s*responsable[:\s]*(.+?))?(?:\s*[-\u2013|]\s*fecha[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4}))?\s*$",
    re.IGNORECASE,
)


def parse_acta_pdf(file_content: bytes) -> ActaParsedResult:
    """Extract structured data from an acta PDF.

    Supports multi-service actas: looks for 'Servicio:' markers to split sections.
    On failure, raises ActaFormatError or ActaExtractionError with detail.
    """
    try:
        pdf = pdfplumber.open(BytesIO(file_content))
    except Exception as e:
        raise ActaFormatError(f"No se pudo abrir el PDF: {e}")

    if not pdf.pages:
        raise ActaFormatError("El PDF no contiene p\u00e1ginas")

    # Extract full text
    full_text = ""
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"

    if not full_text.strip():
        raise ActaFormatError(
            "No se pudo extraer texto del PDF",
            details=["El PDF puede ser una imagen escaneada. Solo se soportan PDFs con texto seleccionable."],
        )

    warnings: list[str] = []
    services: list[ActaParsedService] = []

    # Try to find date (global for the acta)
    date_match = _DATE_PATTERN.search(full_text)
    global_date = ""
    if date_match:
        day, month, year = date_match.group(1), date_match.group(2), date_match.group(3)
        global_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    else:
        warnings.append("No se encontr\u00f3 fecha de reuni\u00f3n en el documento")

    # Split by service markers
    lines = full_text.split("\n")
    current_service: ActaParsedService | None = None
    in_proposals = False
    in_attendees = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Check for service marker
        svc_match = _SERVICE_PATTERN.match(stripped)
        if svc_match:
            if current_service:
                services.append(current_service)
            current_service = ActaParsedService(
                servicio_nombre=svc_match.group(1).strip(),
                fecha_reunion=global_date,
            )
            in_proposals = False
            in_attendees = False
            continue

        # Check for attendees section
        att_match = _ATTENDEES_PATTERN.match(stripped)
        if att_match:
            in_attendees = True
            in_proposals = False
            inline = att_match.group(1).strip()
            if inline and current_service:
                current_service.asistentes.extend(
                    [a.strip() for a in re.split(r"[,;]", inline) if a.strip()]
                )
            continue

        # Check for proposals section
        if _PROPOSALS_HEADER.search(stripped):
            in_proposals = True
            in_attendees = False
            continue

        if current_service is None:
            # No service marker found yet \u2014 create a default one
            if not services:
                current_service = ActaParsedService(
                    servicio_nombre="(sin identificar)",
                    fecha_reunion=global_date,
                )
                warnings.append(
                    "No se encontr\u00f3 marcador 'Servicio:' \u2014 contenido asignado a servicio sin identificar"
                )

        if current_service is None:
            continue

        # Parse content based on current section
        if in_proposals:
            prop_match = _PROPOSAL_ROW.match(stripped)
            if prop_match:
                proposal: dict = {"descripcion": prop_match.group(1).strip()}
                if prop_match.group(2):
                    proposal["responsable"] = prop_match.group(2).strip()
                if prop_match.group(3):
                    raw_date = prop_match.group(3).strip()
                    parts = re.split(r"[/\-\.]", raw_date)
                    if len(parts) == 3:
                        proposal["fecha_compromiso"] = (
                            f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                        )
                current_service.propuestas.append(proposal)
            else:
                # Could be continuation text of proposals section
                if stripped.startswith(("-", "\u2022", "*")):
                    current_service.propuestas.append(
                        {"descripcion": stripped.lstrip("-\u2022* ").strip()}
                    )
        elif in_attendees:
            # Lines in attendees section (one per line or comma-separated)
            attendees = [a.strip() for a in re.split(r"[,;]", stripped) if a.strip()]
            current_service.asistentes.extend(attendees)
        else:
            # General content \u2014 append to puntos_tratados
            if current_service.puntos_tratados:
                current_service.puntos_tratados += "\n" + stripped
            else:
                current_service.puntos_tratados = stripped

    # Don't forget the last service
    if current_service:
        services.append(current_service)

    if not services:
        raise ActaExtractionError(
            "No se pudo extraer informaci\u00f3n de servicios del acta",
            details=[
                "Verifique que el acta contiene marcadores 'Servicio:' o contenido estructurado reconocible"
            ],
        )

    return ActaParsedResult(services=services, raw_text=full_text, warnings=warnings)
