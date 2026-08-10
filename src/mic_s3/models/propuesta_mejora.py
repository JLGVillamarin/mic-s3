from sqlalchemy import String, ForeignKey, Date, Text, Enum as SAEnum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from mic_s3.models.base import Base
from datetime import date, datetime
import enum


class EstadoPropuesta(str, enum.Enum):
    PENDIENTE = "pendiente"
    EN_CURSO = "en_curso"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"


class PropuestaMejora(Base):
    __tablename__ = "propuestas_mejora"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    servicio_id: Mapped[int] = mapped_column(ForeignKey("servicios.id"), nullable=False)
    acta_id: Mapped[int | None] = mapped_column(ForeignKey("actas.id"))
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    responsable: Mapped[str] = mapped_column(String(200), nullable=False)
    fecha_compromiso: Mapped[date] = mapped_column(Date, nullable=False)
    estado: Mapped[EstadoPropuesta] = mapped_column(SAEnum(EstadoPropuesta), default=EstadoPropuesta.PENDIENTE)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    servicio: Mapped["Servicio"] = relationship(back_populates="propuestas_mejora")
    acta: Mapped["Acta | None"] = relationship(back_populates="propuestas_mejora")
