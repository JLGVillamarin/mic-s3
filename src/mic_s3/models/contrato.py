from sqlalchemy import ForeignKey, Numeric, Date, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from mic_s3.models.base import Base
from datetime import date
from decimal import Decimal


class Contrato(Base):
    __tablename__ = "contratos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    servicio_id: Mapped[int] = mapped_column(ForeignKey("servicios.id"), nullable=False, unique=True)
    horas_contratadas_mes: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    perfiles_contratados: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date | None] = mapped_column(Date)

    servicio: Mapped["Servicio"] = relationship(back_populates="contrato")
