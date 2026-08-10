from sqlalchemy import String, ForeignKey, Text, Boolean, Enum as SAEnum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from mic_s3.models.base import Base
from datetime import datetime
import enum


class TipoAlerta(str, enum.Enum):
    DESVIACION_HORAS = "desviacion_horas"
    COBERTURA_INSUFICIENTE = "cobertura_insuficiente"
    PROPUESTA_VENCIDA = "propuesta_vencida"
    CONTRATO_PROXIMO_VENCER = "contrato_proximo_vencer"


class SeveridadAlerta(str, enum.Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class Alerta(Base):
    __tablename__ = "alertas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    servicio_id: Mapped[int] = mapped_column(ForeignKey("servicios.id"), nullable=False)
    tipo: Mapped[TipoAlerta] = mapped_column(SAEnum(TipoAlerta), nullable=False)
    severidad: Mapped[SeveridadAlerta] = mapped_column(SAEnum(SeveridadAlerta), nullable=False)
    mensaje: Mapped[str] = mapped_column(Text, nullable=False)
    fecha_generacion: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    resuelta: Mapped[bool] = mapped_column(Boolean, default=False)

    servicio: Mapped["Servicio"] = relationship(back_populates="alertas")
