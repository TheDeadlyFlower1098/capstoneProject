
from flask import Flask, Blueprint, render_template, session
from flask import Blueprint, render_template, session
from flask import Blueprint, render_template, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from flask import request, flash, redirect, url_for
from werkzeug.security import generate_password_hash
from flask import request, redirect, url_for, render_template, flash, session
from werkzeug.security import check_password_hash

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

main_bp = Blueprint("main", __name__)

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
    __tablename__ = "users" # Explicitly naming this helps ForeignKey find it
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    password:Mapped[str] = mapped_column(String(255), nullable=False)

    profile_pic: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[str] = mapped_column(String(50), nullable=True)

# --- APP SETUP ---
app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.secret_key = "planit"  # replace with something random and secure
# app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:root@localhost/planit_db"
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:cset155@localhost/planit_db"

db.init_app(app)

main_bp = Blueprint("main", __name__)

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
    current_user_id = session.get("user_id")

    user = db.session.execute(db.select(User).filter_by(id=current_user_id)).scalar()

    query = db.select(Task).filter_by(user_id=current_user_id).order_by(Task.id.asc())
    tasks = db.session.execute(query).scalars().all()

    return render_template("newTasks.html", user=user, tasks=tasks, active_page="newTasks")

@main_bp.route("/settings")
def settings():
    return render_template("settings.html", active_page="settings")



@main_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        password = request.form.get("password")

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered.", "error")
            return redirect(url_for("main.register"))

        # Hash the password before storing
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')


        # Create new user
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("main.login"))

    return render_template("register.html")
@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # 1. Find the user by email
        user = User.query.filter_by(email=email).first()

        if user:
            # 2. Check hashed password
            if check_password_hash(user.password, password):
                # 3. Store user ID in session
                session['user_id'] = user.id
                flash("Logged in successfully!", "success")
                return redirect(url_for("main.dashboard"))
            else:
                flash("Incorrect password.", "error")
        else:
            flash("Email not registered.", "error")

    # GET request or failed login
    return render_template("login.html")




app.register_blueprint(main_bp)

# --- INITIALIZE DATABASE ---
with app.app_context():
    db.create_all() 