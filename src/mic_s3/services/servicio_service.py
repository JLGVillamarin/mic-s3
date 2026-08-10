from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from mic_s3.models.servicio import Servicio
from mic_s3.models.area import Area
from mic_s3.models.contrato import Contrato


class ServicioService:
    def __init__(self, session: Session):
        self.session = session

    def list_all(self) -> list[Servicio]:
        stmt = select(Servicio).options(joinedload(Servicio.area), joinedload(Servicio.contrato))
        return list(self.session.scalars(stmt).unique())

    def get_by_id(self, servicio_id: int) -> Servicio | None:
        stmt = select(Servicio).where(Servicio.id == servicio_id).options(
            joinedload(Servicio.area), joinedload(Servicio.contrato)
        )
        return self.session.scalars(stmt).unique().one_or_none()

    def create(self, data: dict) -> Servicio:
        contrato_data = data.pop("contrato", None)
        servicio = Servicio(**data)
        self.session.add(servicio)
        self.session.flush()
        if contrato_data:
            contrato = Contrato(servicio_id=servicio.id, **contrato_data)
            self.session.add(contrato)
        self.session.commit()
        self.session.refresh(servicio)
        return servicio

    def update(self, servicio_id: int, data: dict) -> Servicio | None:
        servicio = self.get_by_id(servicio_id)
        if not servicio:
            return None
        contrato_data = data.pop("contrato", None)
        for key, value in data.items():
            setattr(servicio, key, value)
        if contrato_data and servicio.contrato:
            for key, value in contrato_data.items():
                setattr(servicio.contrato, key, value)
        elif contrato_data:
            contrato = Contrato(servicio_id=servicio.id, **contrato_data)
            self.session.add(contrato)
        self.session.commit()
        self.session.refresh(servicio)
        return servicio

    def delete(self, servicio_id: int) -> bool:
        servicio = self.session.get(Servicio, servicio_id)
        if not servicio:
            return False
        self.session.delete(servicio)
        self.session.commit()
        return True
