from sqlalchemy import ForeignKey, Date, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from mic_s3.models.base import Base
from datetime import date, datetime
from sqlalchemy import func, DateTime


class Acta(Base):
    __tablename__ = "actas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    servicio_id: Mapped[int] = mapped_column(ForeignKey("servicios.id"), nullable=False)
    fecha_reunion: Mapped[date] = mapped_column(Date, nullable=False)
    asistentes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    puntos_tratados: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    servicio: Mapped["Servicio"] = relationship(back_populates="actas")
    propuestas_mejora: Mapped[list["PropuestaMejora"]] = relationship(back_populates="acta")
