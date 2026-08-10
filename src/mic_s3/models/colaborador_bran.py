from sqlalchemy import String, ForeignKey, Date, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from mic_s3.models.base import Base
from datetime import date


class ColaboradorBran(Base):
    __tablename__ = "colaboradores_bran"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    servicio_id: Mapped[int] = mapped_column(ForeignKey("servicios.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(300), nullable=False)
    perfil: Mapped[str] = mapped_column(String(200), nullable=False)
    mes: Mapped[date] = mapped_column(Date, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    servicio: Mapped["Servicio"] = relationship(back_populates="colaboradores_bran")
