from datetime import date
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from mic_s3.models.servicio import Servicio
from mic_s3.models.colaborador_bran import ColaboradorBran
from mic_s3.parsers.bran_parser import parse_bran_excel, BranRow, BranParserError


class BranImportResult:
    def __init__(self):
        self.rows: list[BranRow] = []
        self.warnings: list[str] = []
        self.servicios_not_found: list[str] = []
        self.total_parsed: int = 0


class BranImportService:
    def __init__(self, session: Session):
        self.session = session

    def preview(self, file_content: bytes) -> BranImportResult:
        """Parse and validate without persisting."""
        result = BranImportResult()
        rows = parse_bran_excel(file_content)
        result.total_parsed = len(rows)
        result.rows = rows

        # Check which servicios exist
        servicio_names = {r.servicio_nombre for r in rows}
        existing = self.session.scalars(
            select(Servicio).where(Servicio.nombre.in_(servicio_names))
        ).all()
        existing_names = {s.nombre for s in existing}
        result.servicios_not_found = list(servicio_names - existing_names)

        if result.servicios_not_found:
            result.warnings.append(
                f"Servicios no encontrados: {', '.join(result.servicios_not_found)}"
            )

        return result

    def confirm(self, file_content: bytes, mes: date) -> dict:
        """Parse and persist monthly snapshot rows."""
        rows = parse_bran_excel(file_content)

        # Map servicio names to IDs
        servicio_names = {r.servicio_nombre for r in rows}
        servicios = self.session.scalars(
            select(Servicio).where(Servicio.nombre.in_(servicio_names))
        ).all()
        name_to_id = {s.nombre: s.id for s in servicios}

        created = 0
        skipped = 0
        for row in rows:
            servicio_id = name_to_id.get(row.servicio_nombre)
            if not servicio_id:
                skipped += 1
                continue

            # Check if already exists for this month
            existing = self.session.scalars(
                select(ColaboradorBran).where(
                    and_(
                        ColaboradorBran.servicio_id == servicio_id,
                        ColaboradorBran.nombre == row.nombre,
                        ColaboradorBran.mes == mes,
                    )
                )
            ).first()

            if existing:
                existing.activo = True
                existing.perfil = row.perfil
            else:
                colaborador = ColaboradorBran(
                    servicio_id=servicio_id,
                    nombre=row.nombre,
                    perfil=row.perfil,
                    mes=mes,
                    activo=True,
                )
                self.session.add(colaborador)
                created += 1

        # Mark collaborators NOT in this import as inactive for this month
        for servicio_id in name_to_id.values():
            imported_names = [r.nombre for r in rows if name_to_id.get(r.servicio_nombre) == servicio_id]
            stmt = select(ColaboradorBran).where(
                and_(
                    ColaboradorBran.servicio_id == servicio_id,
                    ColaboradorBran.mes == mes,
                    ColaboradorBran.nombre.notin_(imported_names),
                )
            )
            for colab in self.session.scalars(stmt):
                colab.activo = False

        self.session.commit()
        return {"created": created, "skipped": skipped, "total": len(rows)}
