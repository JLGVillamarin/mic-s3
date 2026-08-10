"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-08-10
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # areas
    op.create_table(
        "areas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("responsable", sa.String(200), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nombre"),
    )
    # servicios
    op.create_table(
        "servicios",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nombre", sa.String(300), nullable=False),
        sa.Column("area_id", sa.Integer(), nullable=False),
        sa.Column("proveedor", sa.String(200), nullable=False),
        sa.Column("estado", sa.Enum("activo", "inactivo", "en_transicion", name="estadoservicio"), nullable=True),
        sa.ForeignKeyConstraint(["area_id"], ["areas.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    # contratos
    op.create_table(
        "contratos",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("servicio_id", sa.Integer(), nullable=False),
        sa.Column("horas_contratadas_mes", sa.Numeric(10, 2), nullable=False),
        sa.Column("perfiles_contratados", sa.JSON(), nullable=False),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("fecha_fin", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["servicio_id"], ["servicios.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("servicio_id"),
    )
    # colaboradores_bran
    op.create_table(
        "colaboradores_bran",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("servicio_id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(300), nullable=False),
        sa.Column("perfil", sa.String(200), nullable=False),
        sa.Column("mes", sa.Date(), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["servicio_id"], ["servicios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    # actas
    op.create_table(
        "actas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("servicio_id", sa.Integer(), nullable=False),
        sa.Column("fecha_reunion", sa.Date(), nullable=False),
        sa.Column("asistentes", sa.JSON(), nullable=False),
        sa.Column("puntos_tratados", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["servicio_id"], ["servicios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    # ejecuciones_mensuales
    op.create_table(
        "ejecuciones_mensuales",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("servicio_id", sa.Integer(), nullable=False),
        sa.Column("mes", sa.Date(), nullable=False),
        sa.Column("horas_reales", sa.Numeric(10, 2), nullable=False),
        sa.Column("horas_teoricas", sa.Numeric(10, 2), nullable=False),
        sa.ForeignKeyConstraint(["servicio_id"], ["servicios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    # propuestas_mejora
    op.create_table(
        "propuestas_mejora",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("servicio_id", sa.Integer(), nullable=False),
        sa.Column("acta_id", sa.Integer(), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("responsable", sa.String(200), nullable=False),
        sa.Column("fecha_compromiso", sa.Date(), nullable=False),
        sa.Column("estado", sa.Enum("pendiente", "en_curso", "completada", "cancelada", name="estadopropuesta"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["servicio_id"], ["servicios.id"]),
        sa.ForeignKeyConstraint(["acta_id"], ["actas.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    # alertas
    op.create_table(
        "alertas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("servicio_id", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.Enum("desviacion_horas", "cobertura_insuficiente", "propuesta_vencida", "contrato_proximo_vencer", name="tipoalerta"), nullable=False),
        sa.Column("severidad", sa.Enum("baja", "media", "alta", "critica", name="severidadalerta"), nullable=False),
        sa.Column("mensaje", sa.Text(), nullable=False),
        sa.Column("fecha_generacion", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column("resuelta", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["servicio_id"], ["servicios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("alertas")
    op.drop_table("propuestas_mejora")
    op.drop_table("ejecuciones_mensuales")
    op.drop_table("actas")
    op.drop_table("colaboradores_bran")
    op.drop_table("contratos")
    op.drop_table("servicios")
    op.drop_table("areas")
    op.execute("DROP TYPE IF EXISTS estadoservicio")
    op.execute("DROP TYPE IF EXISTS estadopropuesta")
    op.execute("DROP TYPE IF EXISTS tipoalerta")
    op.execute("DROP TYPE IF EXISTS severidadalerta")
