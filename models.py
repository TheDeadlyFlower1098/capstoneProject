from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import (
    DateTime, String, Numeric, ForeignKey, Boolean,
    Integer, Text, Date, Time, Enum,
    UniqueConstraint, CheckConstraint, Index
)
from extensions import db
from datetime import datetime
import random
import string

# ---------------- BASE ---------------- #
class Base(DeclarativeBase):
    pass


# ---------------- ENUMS ---------------- #
friendship_status_enum = Enum(
    "pending", "accepted", "declined",
    name="friendship_status",
    native_enum=True
)

invite_status_enum = Enum(
    "pending", "accepted", "declined",
    name="invite_status",
    native_enum=True
)

event_visibility_enum = Enum(
    "private", "friends", "public",
    name="event_visibility",
    native_enum=True
)

# ---------------- USER ---------------- #
class User(db.Model, UserMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_code: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False,
        default=lambda: User.generate_user_code()
    )
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_pic: Mapped[str] = mapped_column(String(255), default="default.png")
    balance: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    goal: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0) # Add this line
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    sent_requests = relationship("Friendship", foreign_keys="Friendship.user_id", back_populates="requester", cascade="all, delete-orphan")
    received_requests = relationship("Friendship", foreign_keys="Friendship.friend_id", back_populates="receiver", cascade="all, delete-orphan")
    created_events = relationship("Event", back_populates="creator", cascade="all, delete-orphan")
    invites = relationship("EventInvite", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")

    @staticmethod
    def generate_user_code(length=8):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        return f"PLANIT-{code}"

# ---------------- FRIENDSHIP ---------------- #
class Friendship(db.Model):
    __tablename__ = "friendships"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    friend_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(friendship_status_enum, default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    requester = relationship("User", foreign_keys=[user_id], back_populates="sent_requests")
    receiver = relationship("User", foreign_keys=[friend_id], back_populates="received_requests")

    __table_args__ = (
        UniqueConstraint("user_id", "friend_id", name="uq_friendship_pair"),
        CheckConstraint("user_id != friend_id", name="ck_no_self_friend"),
        Index("ix_friend_user", "user_id"),
        Index("ix_friend_friend", "friend_id"),
    )

# ---------------- BLOCKING USERS ---------------- #
class UserBlock(db.Model):
    __tablename__ = "user_blocks"

    id: Mapped[int] = mapped_column(primary_key=True)

    blocker_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    blocked_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow
    )

    blocker = relationship("User", foreign_keys=[blocker_id])
    blocked = relationship("User", foreign_keys=[blocked_id])

    __table_args__ = (
        UniqueConstraint("blocker_id", "blocked_id", name="uq_user_block"),
        CheckConstraint("blocker_id != blocked_id", name="ck_no_self_block"),
        Index("ix_blocker", "blocker_id"),
        Index("ix_blocked", "blocked_id"),
    )

# ---------------- TASK ---------------- #
class Task(db.Model):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    list_name: Mapped[str] = mapped_column(String(50), nullable=False)
    task_name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    user = relationship("User", back_populates="tasks")

    __table_args__ = (
        Index("ix_task_user", "user_id"),
    )

# ---------------- TRANSACTION ---------------- #
class Transaction(db.Model):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    budget_limit: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    transaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default='General', nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    user = relationship("User", back_populates="transactions")

    __table_args__ = (
        Index("ix_tx_user", "user_id"),
    )

# ---------------- EVENT ---------------- #
class Event(db.Model):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    location: Mapped[str] = mapped_column(String(255))
    visibility: Mapped[str] = mapped_column(event_visibility_enum, default="private", nullable=False)
    repeat_type = db.Column(db.String(20))
    start_date: Mapped[Date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Date] = mapped_column(Date)
    start_time: Mapped[Time] = mapped_column(Time)
    end_time: Mapped[Time] = mapped_column(Time)
    all_day: Mapped[bool] = mapped_column(Boolean, default=False)
    color: Mapped[str] = mapped_column(String(20), default="blue")
    reminder_minutes_before: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = relationship("User", back_populates="created_events")
    invites = relationship("EventInvite", back_populates="event", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_event_creator", "creator_id"),
        Index("ix_event_start_date", "start_date"),
    )

# ---------------- EVENT INVITE ---------------- #
class EventInvite(db.Model):
    __tablename__ = "event_invitations"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    invited_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(invite_status_enum, default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    event = relationship("Event", back_populates="invites")
    user = relationship("User", back_populates="invites")

    __table_args__ = (
        UniqueConstraint("event_id", "invited_user_id", name="uq_event_invite_unique"),
        Index("ix_invited_user", "invited_user_id"),
    )