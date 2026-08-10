from datetime import date
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from mic_s3.models.servicio import Servicio
from mic_s3.models.contrato import Contrato
from mic_s3.models.colaborador_bran import ColaboradorBran


class DimensionamientoResult:
    def __init__(self):
        self.servicio_id: int = 0
        self.servicio_nombre: str = ""
        self.mes: str = ""
        self.perfiles: list[dict] = []  # [{perfil, contratados, activos, diferencia}]
        self.total_contratados: int = 0
        self.total_activos: int = 0
        self.cobertura_pct: float = 0.0


class DimensionamientoService:
    def __init__(self, session: Session):
        self.session = session

    def comparar(self, servicio_id: int, mes: date) -> DimensionamientoResult | None:
        """Compare contracted profiles vs active BRAN collaborators for a given month."""
        servicio = self.session.get(Servicio, servicio_id)
        if not servicio:
            return None

        result = DimensionamientoResult()
        result.servicio_id = servicio_id
        result.servicio_nombre = servicio.nombre
        result.mes = mes.isoformat()

        # Get contracted profiles from contrato
        contrato = self.session.scalars(
            select(Contrato).where(Contrato.servicio_id == servicio_id)
        ).first()

        perfiles_contratados: dict[str, int] = {}
        if contrato and contrato.perfiles_contratados:
            perfiles_contratados = {k: int(v) for k, v in contrato.perfiles_contratados.items()}

        # Get active collaborators for this month
        colaboradores = list(self.session.scalars(
            select(ColaboradorBran).where(
                and_(
                    ColaboradorBran.servicio_id == servicio_id,
                    ColaboradorBran.mes == mes,
                    ColaboradorBran.activo == True,
                )
            )
        ))

        # Count activos by perfil
        activos_por_perfil: dict[str, int] = {}
        for c in colaboradores:
            activos_por_perfil[c.perfil] = activos_por_perfil.get(c.perfil, 0) + 1

        # Merge all profiles
        all_perfiles = set(list(perfiles_contratados.keys()) + list(activos_por_perfil.keys()))

        for perfil in sorted(all_perfiles):
            contratados = perfiles_contratados.get(perfil, 0)
            activos = activos_por_perfil.get(perfil, 0)
            result.perfiles.append({
                "perfil": perfil,
                "contratados": contratados,
                "activos": activos,
                "diferencia": activos - contratados,
            })
            result.total_contratados += contratados
            result.total_activos += activos

        if result.total_contratados > 0:
            result.cobertura_pct = round((result.total_activos / result.total_contratados) * 100, 1)
        else:
            result.cobertura_pct = 100.0 if result.total_activos == 0 else 0.0

        return result
