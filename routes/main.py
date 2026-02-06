from flask import Blueprint, render_template, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

main_bp = Blueprint("main", __name__)

# --- DATABASE MODELS ----
class Task(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    task_name: Mapped[str] = mapped_column(String(200), nullable=False)
    list_name: Mapped[str] = mapped_column(String(100), default="Grocery List")
    is_completed: Mapped[bool] = mapped_column(default=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)

class Transaction(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    transaction_date: Mapped[str] = mapped_column(String(50))
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)

class User(db.Model):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    profile_pic: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[str] = mapped_column(String(50), nullable=True)

# --- ROUTES ---
@main_bp.route("/")
def home():
    return render_template("home.html")

@main_bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", active_page="dashboard")

@main_bp.route("/friends")
def friends():
    return render_template("friends.html", active_page="friends")

@main_bp.route("/budget")
def budget():
    current_user_id = session.get("user_id")

    user = db.session.execute(
        db.select(User).filter_by(id=current_user_id)
    ).scalar()

    query = db.select(Transaction).filter_by(user_id=current_user_id).order_by(Transaction.id.desc())
    all_transactions = db.session.execute(query).scalars().all()

    return render_template("budget.html", user=user, transactions=all_transactions, active_page="budget")

@main_bp.route("/calendar")
def calendar():
    return render_template("calendar.html", active_page="calendar")

@main_bp.route("/newTasks")
def todo_list():
    current_user_id = session.get("user_id")

    user = db.session.execute(db.select(User).filter_by(id=current_user_id)).scalar()

    query = db.select(Task).filter_by(user_id=current_user_id).order_by(Task.id.asc())
    tasks = db.session.execute(query).scalars().all()

    return render_template("newTasks.html", user=user, tasks=tasks, active_page="newTasks")

@main_bp.route("/settings")
def settings():
    return render_template("settings.html", active_page="settings")
