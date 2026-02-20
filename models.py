from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session
from sqlalchemy import DateTime, String, Numeric, ForeignKey, Boolean, Integer, TIMESTAMP, event, Text, Date, Time, Enum
from werkzeug.security import generate_password_hash
from datetime import datetime
import random
import string

# ---------------- BASE & DB ---------------- #
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# ---------------- MODELS ---------------- #
class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_code: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, default=lambda: User.generate_user_code()
    )
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_pic: Mapped[str] = mapped_column(String(255), default="default.png")
    created_at: Mapped[str] = mapped_column(TIMESTAMP, default=db.func.current_timestamp())

    # Friendships
    sent_requests = relationship(
        "Friendship",
        foreign_keys="Friendship.user_id",
        back_populates="requester",
        cascade="all, delete-orphan"
    )

    received_requests = relationship(
        "Friendship",
        foreign_keys="Friendship.friend_id",
        back_populates="receiver",
        cascade="all, delete-orphan"
    )

    @staticmethod
    def generate_user_code(length=8):
        import random, string
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        return f"PLANIT-{code}"


class Friendship(db.Model):
    __tablename__ = "friendships"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    friend_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum('pending', 'accepted', name='friendship_status'), default='pending') # pending/accepted
    created_at: Mapped[str] = mapped_column(TIMESTAMP, default=db.func.current_timestamp())

    # Backrefs
    requester = relationship("User", foreign_keys=[user_id], back_populates="sent_requests")
    receiver = relationship("User", foreign_keys=[friend_id], back_populates="received_requests")


class Task(db.Model):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)


class Transaction(db.Model):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    transaction_date: Mapped[str] = mapped_column(String(50))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

class Event(db.Model):
    __tablename__ = "events"

    id = mapped_column(Integer, primary_key=True)
    creator_id = mapped_column(ForeignKey("users.id"), nullable=False)
    title = mapped_column(String(150), nullable=False)
    description = mapped_column(Text)
    location = mapped_column(String(255))  # match DB length
    tag = mapped_column(String(20))
    event_date = mapped_column(Date, nullable=False)
    end_date = mapped_column(Date)
    start_time = mapped_column(Time)
    end_time = mapped_column(Time)
    all_day = mapped_column(Boolean, default=False)
    color = mapped_column(String(20), default="blue")
    is_private = mapped_column(Boolean, default=False)
    allow_invited_to_see_details = mapped_column(Boolean, default=True)
    reminder_minutes_before = mapped_column(Integer)
    created_at = mapped_column(DateTime, default=datetime.utcnow)
    updated_at = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    invites = db.relationship(
        "EventInvite",
        back_populates="event",
        cascade="all, delete-orphan"
    )

class EventInvite(db.Model):
    __tablename__ = "event_invitations"

    id = mapped_column(Integer, primary_key=True)
    event_id = mapped_column(ForeignKey("events.id"), nullable=False)
    invited_user_id = mapped_column(ForeignKey("users.id"), nullable=False)

    status = mapped_column(String(20), default="pending")
    created_at = mapped_column(DateTime, default=datetime.utcnow)

    # relationships
    event = db.relationship("Event", back_populates="invites")
    user = db.relationship("User", foreign_keys=[invited_user_id])