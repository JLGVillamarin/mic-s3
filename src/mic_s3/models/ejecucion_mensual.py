from sqlalchemy import ForeignKey, Date, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from mic_s3.models.base import Base
from datetime import date
from decimal import Decimal


class EjecucionMensual(Base):
    __tablename__ = "ejecuciones_mensuales"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    servicio_id: Mapped[int] = mapped_column(ForeignKey("servicios.id"), nullable=False)
    mes: Mapped[date] = mapped_column(Date, nullable=False)
    horas_reales: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    horas_teoricas: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    servicio: Mapped["Servicio"] = relationship(back_populates="ejecuciones_mensuales")
