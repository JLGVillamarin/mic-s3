from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from mic_s3.models.base import Base


class Area(Base):
    __tablename__ = "areas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    responsable: Mapped[str | None] = mapped_column(String(200))

    servicios: Mapped[list["Servicio"]] = relationship(back_populates="area")
