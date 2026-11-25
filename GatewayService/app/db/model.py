from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List
import uuid

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import (String, Enum as SQLEnum, text, ForeignKey, Numeric, UniqueConstraint,
                        DateTime, Integer, Boolean)

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


class OrderItemStatus(str, Enum):
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
    
    name: Mapped[str] = mapped_column(String(100))
    surname: Mapped[str] = mapped_column(String(100))
    
    type: Mapped[str] = mapped_column(String(100))

    __mapper_args__ = {
        "polymorphic_identity": "user",
        "polymorphic_on": "type",
    }
    

class Client(User):
    __tablename__ = "client_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        primary_key=True
    )
    phone: Mapped[Optional[str]] = mapped_column(String(20))

    __mapper_args__ = {
        "polymorphic_identity": "client"
    }
    
    orders: Mapped[List["Order"]] = relationship(
        back_populates="client", 
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    cart: Mapped[Optional["Cart"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="joined",
        uselist=False,
    )


class Partner(User):
    __tablename__ = "partner_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )

    company_name: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    address: Mapped[Optional[str]] = mapped_column(String(255))

    __mapper_args__ = {
        "polymorphic_identity": "partner",
    }

    paintings: Mapped[List["Painting"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class Painting(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "paintings"

    #id, created_at, updated_at из миксинов

    partner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("partner_profiles.id", ondelete="CASCADE"),
        nullable=False, 
        index=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    creation_year: Mapped[Optional[int]] = mapped_column(Integer)
    # description
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    rent_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))

    status: Mapped[PaintingStatus] = mapped_column(
        SQLEnum(PaintingStatus, name="painting_status_enum"),
        default=PaintingStatus.AVAILABLE, 
        index=True
    )

    # --- Relationships ---
    owner: Mapped["Partner"] = relationship(back_populates="paintings", lazy="selectin")
    order_items: Mapped[List["OrderItem"]] = relationship(back_populates="painting", lazy="selectin")
    cart_items: Mapped[List["CartItem"]] = relationship(back_populates="painting", lazy="selectin")


class Order(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "orders"

    #id, created_at, updated_at из миксинов
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("client_profiles.id", ondelete="RESTRICT"), 
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
    client: Mapped["Client"] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(
        back_populates="order", 
        cascade="all, delete-orphan",
        lazy="selectin",
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

    status: Mapped[OrderItemStatus] = mapped_column(
        SQLEnum(OrderItemStatus, name="order_item_status_enum"),
        default=OrderItemStatus.CREATED
    )

    type: Mapped[OrderItemType] = mapped_column(
        SQLEnum(OrderItemType, name="order_item_type_enum"), 
        default=OrderItemType.RENT
    )

    rental_begin_date: Mapped[Optional[date]] = mapped_column(nullable=True)
    rental_end_date: Mapped[Optional[date]] = mapped_column(nullable=True)

    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # --- Relationships ---
    order: Mapped["Order"] = relationship(back_populates="items")
    painting: Mapped["Painting"] = relationship(back_populates="order_items", lazy="joined")


class Cart(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "carts"

    #id, created_at, updated_at из миксинов
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("client_profiles.id", ondelete="CASCADE"),
        unique=True
    )

    # --- Relationships ---
    user: Mapped["Client"] = relationship(back_populates="cart", lazy="joined")
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
    cart: Mapped["Cart"] = relationship(back_populates="items", lazy="joined")
    painting: Mapped["Painting"] = relationship(back_populates="cart_items", lazy="joined")