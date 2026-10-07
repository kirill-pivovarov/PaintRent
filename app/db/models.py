import enum
import uuid

from datetime import datetime
from enum import Enum


from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Enum as SQLEnum, text, ForeignKey, Text, Numeric, UniqueConstraint, Boolean, DateTime, \
    Integer, func


class Base(DeclarativeBase):
    pass

class UserRole(Enum):
    CLIENT = "CLIENT"
    PARTNER = "PARTNER"
    ADMIN = "ADMIN"


class PaintingStatus(str, enum.Enum):  # Что оставить?
    AVAILABLE = "AVAILABLE"
    RENTED = "RENTED"
    SOLD = "SOLD"
    ARCHIVED = "ARCHIVED"


class OrderStatus(str, enum.Enum):
    CREATED = "CREATED"
    CONFIRMED = "CONFIRMED"
    PAID = "PAID"
    CANCELED = "CANCELED"


class OrderItemType(str, enum.Enum):
    RENT = "RENT"
    PURCHASE = "PURCHASE"


class OrderItemStatus(str, enum.Enum):
    CREATED = "CREATED"
    CONFIRMED = "CONFIRMED"
    PAID = "PAID"
    CANCELED = "CANCELED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    email: Mapped[str] = mapped_column(String(150), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    name: Mapped[str] = mapped_column(String(100))
    surname: Mapped[str] = mapped_column(String(100))

    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole))

    created_at: Mapped[datetime] = mapped_column(
    server_default=text("TIMEZONE('utc', NOW())"))


class Painting(Base):
    __tablename__ = "paintings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    partner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    creation_year: Mapped[int | None] = mapped_column(Integer)
    #description: Mapped[str] = mapped_column(Text)

    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    rent_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    status: Mapped[PaintingStatus] = mapped_column(
        Enum(PaintingStatus, name="painting_st"),
        default=PaintingStatus.AVAILABLE, nullable=False, index=True,)

    created_at: Mapped[datetime] = mapped_column(
        server_default=text("TIMEZONE('utc', NOW())"))

    owner: Mapped["User"] = relationship(back_populates="paintings")
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="painting")
    # cart_items: pass

    # def __repr__(self):
    #     return f"<Painting id={self.id} title={self.title!r} status={self.status}>"



class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)

    status: Mapped[PaintingStatus] = mapped_column(
        Enum(OrderStatus, name="order_st"),
        default=OrderStatus.CREATED, nullable=False,
    )
    
    datetime: Mapped[OrderStatus] = mapped_column(
        DateTime(timezone=True), server_default=func.now())

    total_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)

    created_at: Mapped[datetime] = mapped_column(
        server_default=text("TIMEZONE('utc', NOW())"))

    client: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (UniqueConstraint("order_id", "painting_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)

    painting_id: Mapped[int] = mapped_column(
        ForeignKey("paintings.id", ondelete="RESTRICT"), nullable=False)

    status: Mapped[OrderItemStatus] = mapped_column(
        Enum(OrderItemStatus, name="item_st"), default=OrderItemStatus.CREATED)

    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")
    painting: Mapped["Painting"] = relationship()
    partners: Mapped[list["OrderItemPartner"]] = relationship(
        back_populates="order_item", cascade="all, delete-orphan"
    )
