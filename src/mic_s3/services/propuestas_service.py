from datetime import date
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from mic_s3.models.propuesta_mejora import PropuestaMejora, EstadoPropuesta


class PropuestasService:
    def __init__(self, session: Session):
        self.session = session

    def list_propuestas(
        self,
        servicio_id: int | None = None,
        estado: EstadoPropuesta | None = None,
        overdue: bool = False,
    ) -> list[PropuestaMejora]:
        stmt = select(PropuestaMejora)
        conditions = []
        if servicio_id:
            conditions.append(PropuestaMejora.servicio_id == servicio_id)
        if estado:
            conditions.append(PropuestaMejora.estado == estado)
        if overdue:
            conditions.append(PropuestaMejora.fecha_compromiso < date.today())
            conditions.append(PropuestaMejora.estado.notin_([EstadoPropuesta.COMPLETADA, EstadoPropuesta.CANCELADA]))
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(PropuestaMejora.fecha_compromiso)
        return list(self.session.scalars(stmt))

    def get_by_id(self, propuesta_id: int) -> PropuestaMejora | None:
        return self.session.get(PropuestaMejora, propuesta_id)

    def create(self, data: dict) -> PropuestaMejora:
        propuesta = PropuestaMejora(**data)
        self.session.add(propuesta)
        self.session.commit()
        self.session.refresh(propuesta)
        return propuesta

    def update_estado(self, propuesta_id: int, estado: EstadoPropuesta) -> PropuestaMejora | None:
        propuesta = self.session.get(PropuestaMejora, propuesta_id)
        if not propuesta:
            return None
        propuesta.estado = estado
        self.session.commit()
        self.session.refresh(propuesta)
        return propuesta

    def update(self, propuesta_id: int, data: dict) -> PropuestaMejora | None:
        propuesta = self.session.get(PropuestaMejora, propuesta_id)
        if not propuesta:
            return None
        for key, value in data.items():
            setattr(propuesta, key, value)
        self.session.commit()
        self.session.refresh(propuesta)
        return propuesta

    def delete(self, propuesta_id: int) -> bool:
        propuesta = self.session.get(PropuestaMejora, propuesta_id)
        if not propuesta:
            return False
        self.session.delete(propuesta)
        self.session.commit()
        return True

    def count_overdue(self, servicio_id: int | None = None) -> int:
        stmt = select(PropuestaMejora).where(
            and_(
                PropuestaMejora.fecha_compromiso < date.today(),
                PropuestaMejora.estado.notin_([EstadoPropuesta.COMPLETADA, EstadoPropuesta.CANCELADA]),
            )
        )
        if servicio_id:
            stmt = stmt.where(PropuestaMejora.servicio_id == servicio_id)
        return len(list(self.session.scalars(stmt)))
