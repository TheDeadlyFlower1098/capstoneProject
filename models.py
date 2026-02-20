from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session
from sqlalchemy import String, Numeric, ForeignKey, Boolean, Integer, TIMESTAMP, event
from werkzeug.security import generate_password_hash
import random
import string

# ---------------- BASE & DB ---------------- #
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# ---------------- MODELS ---------------- #
class User(db.Model, UserMixin):
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
    balance: Mapped[int] = mapped_column(Numeric(10, 2), nullable=False, default=0)
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
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/accepted
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
    budget_limit: Mapped[float] = mapped_column(Integer, default=0)
    transaction_date: Mapped[str] = mapped_column(String(50))
    updated_total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default='General', nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

