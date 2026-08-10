from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from mic_s3.models.acta import Acta
from mic_s3.models.propuesta_mejora import EstadoPropuesta, PropuestaMejora
from mic_s3.models.servicio import Servicio
from mic_s3.parsers.acta_pdf_parser import ActaParsedResult, ActaParsedService, parse_acta_pdf


class ActaPreviewResult:
    def __init__(self, parsed: ActaParsedResult):
        self.parsed = parsed
        self.service_mappings: list[dict] = []  # [{parsed_name, matched_id, matched_name, confidence}]
        self.warnings: list[str] = list(parsed.warnings)


class ActaImportService:
    def __init__(self, session: Session):
        self.session = session

    def preview(self, file_content: bytes) -> ActaPreviewResult:
        """Parse PDF and match services without persisting."""
        parsed = parse_acta_pdf(file_content)
        result = ActaPreviewResult(parsed)

        # Try to match parsed service names to DB
        all_servicios = list(self.session.scalars(select(Servicio)))
        name_map = {s.nombre.lower(): s for s in all_servicios}

        for svc in parsed.services:
            parsed_lower = svc.servicio_nombre.lower().strip()
            if parsed_lower in name_map:
                matched = name_map[parsed_lower]
                result.service_mappings.append({
                    "parsed_name": svc.servicio_nombre,
                    "matched_id": matched.id,
                    "matched_name": matched.nombre,
                    "confidence": "exact",
                })
            else:
                # Partial match attempt
                partial = [
                    s
                    for s in all_servicios
                    if parsed_lower in s.nombre.lower() or s.nombre.lower() in parsed_lower
                ]
                if partial:
                    result.service_mappings.append({
                        "parsed_name": svc.servicio_nombre,
                        "matched_id": partial[0].id,
                        "matched_name": partial[0].nombre,
                        "confidence": "partial",
                    })
                    result.warnings.append(
                        f"Servicio '{svc.servicio_nombre}' mapeado parcialmente a '{partial[0].nombre}'"
                    )
                else:
                    result.service_mappings.append({
                        "parsed_name": svc.servicio_nombre,
                        "matched_id": None,
                        "matched_name": None,
                        "confidence": "none",
                    })
                    result.warnings.append(
                        f"Servicio '{svc.servicio_nombre}' no encontrado en la base de datos"
                    )

        return result

    def confirm(self, file_content: bytes, service_mapping: dict[str, int]) -> dict:
        """Persist actas and proposals using user-confirmed service mapping.

        Args:
            file_content: Raw PDF bytes
            service_mapping: {parsed_service_name: servicio_id} confirmed by user
        """
        parsed = parse_acta_pdf(file_content)
        actas_created = 0
        propuestas_created = 0
        skipped = 0

        for svc in parsed.services:
            servicio_id = service_mapping.get(svc.servicio_nombre)
            if not servicio_id:
                skipped += 1
                continue

            # Parse fecha_reunion
            try:
                fecha = date.fromisoformat(svc.fecha_reunion) if svc.fecha_reunion else date.today()
            except ValueError:
                fecha = date.today()

            acta = Acta(
                servicio_id=servicio_id,
                fecha_reunion=fecha,
                asistentes=svc.asistentes,
                puntos_tratados=svc.puntos_tratados or None,
            )
            self.session.add(acta)
            self.session.flush()
            actas_created += 1

            # Create proposals
            for prop in svc.propuestas:
                fecha_compromiso = None
                if prop.get("fecha_compromiso"):
                    try:
                        fecha_compromiso = date.fromisoformat(prop["fecha_compromiso"])
                    except ValueError:
                        fecha_compromiso = None

                propuesta = PropuestaMejora(
                    servicio_id=servicio_id,
                    acta_id=acta.id,
                    descripcion=prop["descripcion"],
                    responsable=prop.get("responsable", "Sin asignar"),
                    fecha_compromiso=fecha_compromiso or fecha,
                    estado=EstadoPropuesta.PENDIENTE,
                )
                self.session.add(propuesta)
                propuestas_created += 1

        self.session.commit()
        return {
            "actas_created": actas_created,
            "propuestas_created": propuestas_created,
            "skipped_services": skipped,
        }
