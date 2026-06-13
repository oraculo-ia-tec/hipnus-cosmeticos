"""
Models de parceiros — revendedores/profissionais que abrem loja Hipnus.

Entidades:
- Partner: pessoa física ou jurídica habilitada a vender produtos Hipnus.
  Cada parceiro é provisionado como uma SUBCONTA (wallet) no Asaas, permitindo
  split de pagamento automático no checkout.

Fluxo financeiro (Asaas Split):
    Cliente paga na loja do parceiro -> Asaas divide:
      - parte para a Hipnus (piso/custo + taxa de plataforma)
      - parte para o parceiro (margem acima do piso)
"""
import enum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin


class PartnerStatus(str, enum.Enum):
    PENDING = "pending"          # cadastrado, aguardando provisionamento Asaas
    ACTIVE = "active"            # subconta Asaas criada e habilitado a vender
    SUSPENDED = "suspended"      # bloqueado temporariamente
    REJECTED = "rejected"        # reprovado no onboarding


class PartnerType(str, enum.Enum):
    PROFISSIONAL = "profissional"   # cabeleireiro / barbeiro
    SALAO = "salao"
    DISTRIBUIDOR = "distribuidor"
    REVENDEDOR = "revendedor"


class Partner(TimestampMixin, Base):
    __tablename__ = "partners"

    # Identificação
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    legal_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    cpf_cnpj: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)

    partner_type: Mapped[PartnerType] = mapped_column(
        Enum(PartnerType), default=PartnerType.REVENDEDOR, nullable=False
    )
    status: Mapped[PartnerStatus] = mapped_column(
        Enum(PartnerStatus), default=PartnerStatus.PENDING, nullable=False, index=True
    )

    # --- Vínculo com Asaas (subconta / wallet) ---
    # Preenchidos após provisionamento via API oficial do Asaas.
    asaas_account_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    asaas_wallet_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    asaas_api_key: Mapped[str | None] = mapped_column(String(255), nullable=True)  # criptografar em prod

    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Cada parceiro possui uma loja (1:1 no MVP).
    store = relationship(
        "Store", back_populates="partner", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Partner {self.name!r} status={self.status.value}>"
