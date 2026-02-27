
from flask import Flask, Blueprint, render_template, session, request, flash, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Numeric, ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)


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

class User(db.Model, UserMixin):
    __tablename__ = "user"
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


UPLOAD_FOLDER = "static/uploads"

@main_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        file = request.files.get("profile_pic")

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            current_user.profile_pic = filename
            db.session.commit()

            flash("Profile picture updated!", "success")

    return render_template(
        "settings.html",
        active_page="settings",
        user_name=f"{current_user.first_name} {current_user.last_name}"
    )

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
                login_user(user)
                flash("Logged in successfully!", "success")
                return redirect(url_for("main.dashboard"))
            else:
                flash("Incorrect password.", "error")
        else:
            flash("Email not registered.", "error")

    # GET request or failed login
    return render_template("login.html")


#FRIENDS
class FriendRequest(db.Model):
    __tablename__ = "friend_requests"
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    status = db.Column(db.Enum("pending", "accepted", "declined"), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (
        db.UniqueConstraint("sender_id", "receiver_id", name="unique_request"),
    )


class Friend(db.Model):
    __tablename__ = "friends"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (
        db.UniqueConstraint("user_id", "friend_id", name="unique_friendship"),
    )


# Send a friend request by email
@main_bp.route("/friends/request", methods=["POST"])
def send_friend_request():
    sender_id = session.get("user_id")
    if not sender_id:
        return {"error": "Not logged in"}, 401

    email = request.json.get("email")
    if not email:
        return {"error": "Email required"}, 400

    receiver = User.query.filter_by(email=email).first()
    if not receiver:
        return {"error": "User not found"}, 404

    if receiver.id == sender_id:
        return {"error": "Cannot add yourself"}, 400

    # Already friends?
    already_friends = Friend.query.filter_by(user_id=sender_id, friend_id=receiver.id).first()
    if already_friends:
        return {"error": "Already friends"}, 409

    # Existing request?
    existing_request = FriendRequest.query.filter_by(sender_id=sender_id, receiver_id=receiver.id).first()
    if existing_request:
        return {"error": "Request already sent"}, 409

    fr = FriendRequest(sender_id=sender_id, receiver_id=receiver.id)
    db.session.add(fr)
    db.session.commit()

    return {"message": "Friend request sent"}, 201


# Get pending friend requests
@main_bp.route("/friends/requests", methods=["GET"])
def get_friend_requests():
    user_id = session.get("user_id")
    if not user_id:
        return {"error": "Not logged in"}, 401

    requests = (
        db.session.query(FriendRequest, User)
        .join(User, FriendRequest.sender_id == User.id)
        .filter(FriendRequest.receiver_id == user_id, FriendRequest.status == "pending")
        .all()
    )

    return jsonify([
        {
            "request_id": fr.id,
            "sender_id": user.id,
            "name": f"{user.first_name} {user.last_name}",
            "sent_at": fr.created_at.strftime("%Y-%m-%d %H:%M")
        }
        for fr, user in requests
    ])


# Accept a friend request
@main_bp.route("/friends/request/<int:request_id>/accept", methods=["POST"])
def accept_friend_request(request_id):
    user_id = session.get("user_id")
    if not user_id:
        return {"error": "Not logged in"}, 401

    fr = FriendRequest.query.get_or_404(request_id)
    if fr.receiver_id != user_id:
        return {"error": "Unauthorized"}, 403

    fr.status = "accepted"
    # Add bidirectional friendship
    db.session.add(Friend(user_id=user_id, friend_id=fr.sender_id))
    db.session.add(Friend(user_id=fr.sender_id, friend_id=user_id))
    db.session.commit()

    return {"message": "Friend request accepted"}


# Decline a friend request
@main_bp.route("/friends/request/<int:request_id>/decline", methods=["POST"])
def decline_friend_request(request_id):
    user_id = session.get("user_id")
    if not user_id:
        return {"error": "Not logged in"}, 401

    fr = FriendRequest.query.get_or_404(request_id)
    if fr.receiver_id != user_id:
        return {"error": "Unauthorized"}, 403

    fr.status = "declined"
    db.session.commit()

    return {"message": "Friend request declined"}


# Get friends list
@main_bp.route("/friends/list", methods=["GET"])
def get_friends():
    user_id = session.get("user_id")
    if not user_id:
        return {"error": "Not logged in"}, 401

    friends = (
        db.session.query(User)
        .join(Friend, Friend.friend_id == User.id)
        .filter(Friend.user_id == user_id)
        .all()
    )

    return jsonify([
        {
            "id": f.id,
            "name": f"{f.first_name} {f.last_name}"
        }
        for f in friends
    ])


# Search users by name or email
@main_bp.route("/friends/search", methods=["GET"])
def search_users():
    user_id = session.get("user_id")
    if not user_id:
        return {"error": "Not logged in"}, 401

    query = request.args.get("q", "").strip()
    if len(query) < 2:
        return jsonify([])

    users = (
        db.session.query(User)
        .filter(
            User.id != user_id,
            (User.first_name.ilike(f"%{query}%") |
             User.last_name.ilike(f"%{query}%") |
             User.email.ilike(f"%{query}%"))
        )
        .limit(10)
        .all()
    )

    return jsonify([
        {
            "id": u.id,
            "name": f"{u.first_name} {u.last_name}",
            "email": u.email
        }
        for u in users
    ])






# --- Flask-Login setup ---
login_manager = LoginManager()
login_manager.login_view = "main.login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))



app.register_blueprint(main_bp)

# --- INITIALIZE DATABASE ---
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)