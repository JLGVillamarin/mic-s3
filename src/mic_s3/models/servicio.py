from sqlalchemy import String, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from mic_s3.models.base import Base
import enum


class EstadoServicio(str, enum.Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    EN_TRANSICION = "en_transicion"


class Servicio(Base):
    __tablename__ = "servicios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(300), nullable=False)
    area_id: Mapped[int] = mapped_column(ForeignKey("areas.id"), nullable=False)
    proveedor: Mapped[str] = mapped_column(String(200), nullable=False)
    estado: Mapped[EstadoServicio] = mapped_column(SAEnum(EstadoServicio), default=EstadoServicio.ACTIVO)

    area: Mapped["Area"] = relationship(back_populates="servicios")
    contrato: Mapped["Contrato | None"] = relationship(back_populates="servicio", uselist=False)
    colaboradores_bran: Mapped[list["ColaboradorBran"]] = relationship(back_populates="servicio")
    actas: Mapped[list["Acta"]] = relationship(back_populates="servicio")
    ejecuciones_mensuales: Mapped[list["EjecucionMensual"]] = relationship(back_populates="servicio")
    propuestas_mejora: Mapped[list["PropuestaMejora"]] = relationship(back_populates="servicio")
    alertas: Mapped[list["Alerta"]] = relationship(back_populates="servicio")
