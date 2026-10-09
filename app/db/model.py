from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List
import uuid

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import (String, Enum as SQLEnum, text, ForeignKey, Numeric, UniqueConstraint,
                        DateTime, Integer, Boolean, func)

from app.db.mixins import UUIDMixin, TimestampMixin

class Base(DeclarativeBase):
    pass


# ENUMS
class UserRole(str, Enum):
    CLIENT = "CLIENT"
    PARTNER = "PARTNER"
    ADMIN = "ADMIN"


class RentalType(str, Enum):
    RENT = "RENT"
    PURCHASE = "PURCHASE"


class PaintingStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    RENTED = "RENTED"
    SOLD = "SOLD"
    ARCHIVED = "ARCHIVED"


class OrderStatus(str, Enum):
    CREATED = "CREATED"
    CONFIRMED = "CONFIRMED"
    PAID = "PAID"
    CANCELED = "CANCELED"


class OrderItemType(str, Enum):
    RENT = "RENT"
    PURCHASE = "PURCHASE"


# MODELS
class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    #id, created_at, updated_at из миксинов

    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    
    name: Mapped[str] = mapped_column(String(100))
    surname: Mapped[str] = mapped_column(String(100))
    
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole, name="user_st"))

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, server_default="true"
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_anonymized: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default="false"
    )

    # --- Relationships ---
    client_profile: Mapped[Optional["ClientProfile"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    partner_profile: Mapped[Optional["PartnerProfile"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    


class ClientProfile(Base):
    __tablename__ = "client_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        primary_key=True
    )
    phone_number: Mapped[Optional[str]] = mapped_column(String(20))

    # --- Relationships ---
    user: Mapped["User"] = relationship(back_populates="client_profile")
    orders: Mapped[List["Order"]] = relationship(
        back_populates="client", cascade="all, delete-orphan"
    )

    cart: Mapped[Optional["Cart"]] = relationship(
            back_populates="user", cascade="all, delete-orphan", uselist=False
    )


class PartnerProfile(Base):
    __tablename__ = "partner_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )

    company_name: Mapped[Optional[str]] = mapped_column(String(255))
    phone_number: Mapped[Optional[str]] = mapped_column(String(20))
    address: Mapped[Optional[str]] = mapped_column(String(255))

    # --- Relationships ---
    user: Mapped["User"] = relationship(back_populates="partner_profile")
    paintings: Mapped[List["Painting"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class Painting(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "paintings"

    #id, created_at, updated_at из миксинов

    partner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("partner_profiles.user_id", ondelete="CASCADE"),
        nullable=False, 
        index=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    creation_year: Mapped[Optional[int]] = mapped_column(Integer)
    # description
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    rent_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    status: Mapped[PaintingStatus] = mapped_column(
        SQLEnum(PaintingStatus, name="painting_status_enum"),
        default=PaintingStatus.AVAILABLE, 
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        server_default=text("TIMEZONE('utc', NOW())")
    )

    # --- Relationships ---
    owner: Mapped["PartnerProfile"] = relationship(back_populates="paintings")
    order_items: Mapped[List["OrderItem"]] = relationship(back_populates="painting")
    cart_items: Mapped[List["CartItem"]] = relationship(back_populates="painting")


class Order(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "orders"

    #id, created_at, updated_at из миксинов
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("client_profiles.user_id", ondelete="RESTRICT"), 
        nullable=False, 
        index=True
    )

    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus, name="order_st"),
        default=OrderStatus.CREATED, 
        nullable=False
    )

    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0.0)

    # --- Relationships ---
    client: Mapped["ClientProfile"] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(
        back_populates="order", 
        cascade="all, delete-orphan"
    )


class OrderItem(UUIDMixin, Base):
    __tablename__ = "order_items"
    __table_args__ = (UniqueConstraint("order_id", "painting_id"),)

    # id
    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), 
        nullable=False
    )
    painting_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("paintings.id", ondelete="RESTRICT"), 
        nullable=False
    )

    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus, name="order_item_status_enum"), 
        default=OrderStatus.CREATED
    )

    type: Mapped[OrderItemType] = mapped_column(
        SQLEnum(OrderItemType, name="order_item_type_enum"), 
        default=OrderItemType.RENT
    )

    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # --- Relationships ---
    order: Mapped["Order"] = relationship(back_populates="items")
    painting: Mapped["Painting"] = relationship(back_populates="order_items")


class Cart(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "carts"

    #id, created_at, updated_at из миксинов
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("client_profiles.user_id", ondelete="CASCADE"),
        unique=True
    )

    # --- Relationships ---
    user: Mapped["ClientProfile"] = relationship(back_populates="cart")
    items: Mapped[List["CartItem"]] = relationship(
        back_populates="cart",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class CartItem(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("cart_id", "painting_id"),)

    # id, created_at, updated_at из миксинов

    cart_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("carts.id", ondelete="CASCADE"),
        index=True
    )
    painting_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("paintings.id", ondelete="CASCADE"),
        index=True
    )

    rental_type: Mapped[RentalType] = mapped_column(
        SQLEnum(RentalType, name="rental_type_enum"),
        default=RentalType.RENT
    )

    rental_begin_date: Mapped[Optional[date]] = mapped_column()
    rental_end_date: Mapped[Optional[date]] = mapped_column()

    # --- Relationships ---
    cart: Mapped["Cart"] = relationship(back_populates="items")
    painting: Mapped["Painting"] = relationship(back_populates="cart_items")