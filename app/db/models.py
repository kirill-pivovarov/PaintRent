from datetime import datetime, date
from enum import Enum
from typing import Optional, List
import uuid

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Enum as SQLEnum, text, ForeignKey


class Base(DeclarativeBase):
    pass


class UserRole(str, Enum):
    CLIENT = "CLIENT"
    PARTNER = "PARTNER"
    ADMIN = "ADMIN"


class RentalType(str, Enum):
    RENT = "RENT"
    PURCHASE = "PURCHASE"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    
    email: Mapped[str] = mapped_column(String(150), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    
    name: Mapped[str] = mapped_column(String(100))
    surname: Mapped[str] = mapped_column(String(100))
    
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole, name="user_role_enam"))
    
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("TIMEZONE('utc', NOW())")
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("TIMEZONE('utc', NOW())"), 
        onupdate=datetime.now                          
    )


class ClientProfile(Base):
    __tablename__ = "client_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        primary_key=True,
        unique=True
    )
    phone_number: Mapped[str | None] = mapped_column(String(20))

    orders: Mapped[List["Order"]] = relationship(
        back_populates="orders",
        cascade="all, delete-orphan",
        lazy="selectin"
        )


class PartnerProfile(Base):
    __tablename__ = "partner_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        unique=True
    )

    company_name: Mapped[str | None] = mapped_column(String(255))
    phone_number: Mapped[str | None] = mapped_column(String(20))
    address: Mapped[str | None] = mapped_column(String(255))

    paintings: Mapped["Painting"] = relationship(
        back_populates="paintings",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class Cart(Base):
    __tablename__ = "carts"

    # Идентификатор корзины
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # 1-к-1 связь с пользователем (unique=True делает связь строго 1-to-1)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True
    )

    # Дата и время последнего обновления (для фоновой очистки брошенных корзин)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("TIMEZONE('utc', NOW())"),
        onupdate=datetime.now
    )

    # --- Relationships ---
    # Связь с позициями корзины (при удалении корзины удаляются все элементы)
    items: Mapped[List["CartItem"]] = relationship(
        back_populates="cart",
        cascade="all, delete-orphan",
        lazy="selectin"  # Удобно для асинхронного FastAPI (ЛР2)
    )


class CartItem(Base):
    __tablename__ = "cart_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Внешние ключи
    cart_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("carts.id", ondelete="CASCADE"),
        index=True
    )
    painting_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("paintings.id", ondelete="CASCADE"),
        index=True
    )

    # Аренда или Покупка
    rental_type: Mapped[RentalType] = mapped_column(
        SQLEnum(RentalType, name="rental_type_enum"),
        default=RentalType.RENT
    )

    # Необязательные даты (заполняются только если rental_type == RENT)
    rental_begin_date: Mapped[Optional[date]] = mapped_column()
    rental_end_date: Mapped[Optional[date]] = mapped_column()

    created_at: Mapped[datetime] = mapped_column(
        server_default=text("TIMEZONE('utc', NOW())")
    )

    # --- Relationships ---
    cart: Mapped[Cart] = relationship(back_populates="items")
    painting: Mapped["Painting"] = relationship()