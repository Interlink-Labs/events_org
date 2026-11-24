from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Enum
from decimal import Decimal
from database import Base
import enum

class EstimateStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    PAID = "paid"
    CLOSED = "closed"
    CANCELLED = "cancelled"

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class ItemType(str, enum.Enum):
    SERVICE = "service"
    DISCOUNT = "discount"

# --- МОДЕЛИ ЛОКАЦИЙ И УСЛУГ ---
class Venue(Base):
    __tablename__ = "venues"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    address = Column(String)
    capacity = Column(Integer)

class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, index=True)
    venue_id = Column(Integer, ForeignKey("venues.id"))
    name = Column(String)
    description = Column(String, nullable=True)
    price = Column(Numeric(10, 2), default=Decimal("0.00"))
    contact_phone = Column(String, default="Не указан")

# --- МОДЕЛИ СМЕТЫ И ОПЛАТЫ ---
class Estimate(Base):
    __tablename__ = "estimates"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, unique=True, index=True)
    status = Column(Enum(EstimateStatus), default=EstimateStatus.DRAFT)
    
    services_total = Column(Numeric(10, 2), default=Decimal("0.00"))
    expenses_total = Column(Numeric(10, 2), default=Decimal("0.00"))
    total_amount = Column(Numeric(10, 2), default=Decimal("0.00"))
    paid_amount = Column(Numeric(10, 2), default=Decimal("0.00"))
    debt_amount = Column(Numeric(10, 2), default=Decimal("0.00"))
    overpayment_amount = Column(Numeric(10, 2), default=Decimal("0.00"))

class EstimateItem(Base):
    __tablename__ = "estimate_items"
    id = Column(Integer, primary_key=True, index=True)
    estimate_id = Column(Integer, ForeignKey("estimates.id"))
    name = Column(String)
    quantity = Column(Numeric(10, 2))
    unit_price = Column(Numeric(10, 2))
    amount = Column(Numeric(10, 2))
    item_type = Column(Enum(ItemType))

class AdditionalExpense(Base):
    __tablename__ = "additional_expenses"
    id = Column(Integer, primary_key=True, index=True)
    estimate_id = Column(Integer, ForeignKey("estimates.id"))
    name = Column(String)
    amount = Column(Numeric(10, 2))

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    estimate_id = Column(Integer, ForeignKey("estimates.id"))
    amount = Column(Numeric(10, 2))
    method = Column(String, nullable=True)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)

class PaymentLog(Base):
    __tablename__ = "payment_logs"
    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id"))
    action = Column(String)
    old_status = Column(String)
    new_status = Column(String)