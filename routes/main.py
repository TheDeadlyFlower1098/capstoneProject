from flask import Blueprint, render_template, session, request, flash, redirect, url_for, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Task, Transaction, Friendship
from sqlalchemy import or_
from datetime import datetime
main_bp = Blueprint("main", __name__)
login_manager = LoginManager()

# Set the view to redirect to if a user tries to access a @login_required page
login_manager.login_view = "main.login"

def setup_login(app):
    login_manager.init_app(app)
    login_manager.login_view = "main.login"

def create_app():
    # ... inside your app factory or main setup ...
    login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- ROUTES ---------------- #

@main_bp.route("/")
def home():
    if session.get("user_id"):
        return render_template("homeLoggedIn.html", active_page="home")
    return render_template("home.html")

@main_bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", active_page="dashboard")

@main_bp.route("/budget")
@login_required
def budget():
    # Get the most recent transaction to show current budget/limit
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    return render_template("budget.html", active_page="budget", last_transaction=last_transaction)

@main_bp.route("/update-budget", methods=["POST"])
@login_required
def update_budget():
    new_saved = request.form.get('saved_amount')
    new_limit = request.form.get('limit_amount')

    if new_saved and new_limit:
        # 1. Update the User's main balance 
        current_user.balance = float(new_saved)

        # 2. Create a NEW record in the transactions table
        new_transaction = Transaction(
            amount=0, # Or the difference if you're tracking specific changes
            budget_limit=int(new_limit),
            updated_total=float(new_saved),
            user_id=current_user.id,
            transaction_date=datetime.now().strftime("%Y-%m-%d")
        )
        
        db.session.add(new_transaction)
        db.session.commit()
        flash("Budget updated and transaction recorded!", "success")
        
    return redirect(url_for('main.budget'))

@main_bp.route("/calendar")
def calendar():
    return render_template("calendar.html", active_page="calendar")

@main_bp.route("/tasks")
def todo_list():
    return render_template("tasks.html", active_page="tasks")

@main_bp.route("/settings")
def settings():
    return render_template("settings.html", active_page="settings")

# ---------------- AUTH ---------------- #

@main_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        hashed_password = generate_password_hash(request.form.get("password"))
        new_user = User(
            first_name=request.form.get("first_name"),
            last_name=request.form.get("last_name"),
            email=request.form.get("email"),
            password=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()  # user_code is automatically set during flush

        flash("Registered successfully! You can now log in.", "success")
        return redirect(url_for("main.login"))

    return render_template("register.html")

@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form.get("email")).first()
        if user and check_password_hash(user.password, request.form.get("password")):
            # SWAP: session["user_id"] = user.id ->
            login_user(user) 
            flash("Logged in successfully!", "success")
            return redirect(url_for("main.home"))
    return render_template("login.html")

@main_bp.route("/logout")
def logout():
    logout_user() # This is the Flask-Login way
    flash("You have been logged out.", "logout")
    return redirect(url_for("main.home"))

# ---------------- FRIENDS ---------------- #
@main_bp.route("/friends")
def friends():
    user_id = session.get("user_id")
    if not user_id:
        return "Please log in", 401

    user = User.query.get(user_id)

    # Current friends (accepted)
    friendships = Friendship.query.filter(
        ((Friendship.user_id == user.id) | (Friendship.friend_id == user.id)) &
        (Friendship.status == "accepted")
    ).all()

    friends_list = []
    for f in friendships:
        friend = User.query.get(f.friend_id if f.user_id == user.id else f.user_id)
        friends_list.append({
            "id": friend.id,
            "name": f"{friend.first_name} {friend.last_name}",
            "profile_pic": friend.profile_pic,
            "user_code": friend.user_code,
            "last_active": "Today"  # placeholder, you can add real last active logic
        })

    # Incoming friend requests
    pending_requests = Friendship.query.filter_by(friend_id=user.id, status="pending").all()
    requests_list = []
    for r in pending_requests:
        requester = User.query.get(r.user_id)
        requests_list.append({
            "id": requester.id,
            "name": f"{requester.first_name} {requester.last_name}",
            "profile_pic": requester.profile_pic,
            "user_code": requester.user_code
        })

    return render_template(
        "friends.html",
        user_code=user.user_code,
        friends_list=friends_list,
        requests_list=requests_list
    )


# -------------------------------
# ADD FRIEND (SEND REQUEST)
# -------------------------------
@main_bp.route("/friends/add", methods=["POST"])
def add_friend():
    user_id = session.get("user_id")
    data = request.get_json()
    code = data.get("code", "").strip()

    if not code:
        return jsonify({"error": "No friend code provided"}), 400

    # Find the user with that code
    friend = User.query.filter_by(user_code=code).first()
    if not friend or friend.id == user_id:
        return jsonify({"error": "Invalid friend code"}), 404

    # Check if friendship already exists
    existing = Friendship.query.filter(
        ((Friendship.user_id == user_id) & (Friendship.friend_id == friend.id)) |
        ((Friendship.user_id == friend.id) & (Friendship.friend_id == user_id))
    ).first()
    if existing:
        return jsonify({"error": "Friendship already exists"}), 400

    # Create a new friendship request
    new_request = Friendship(user_id=user_id, friend_id=friend.id, status="pending")
    db.session.add(new_request)
    db.session.commit()

    return jsonify({"success": f"Friend request sent to {friend.first_name}"}), 200


# -------------------------------
# ACCEPT FRIEND REQUEST
# -------------------------------
@main_bp.route("/friends/accept", methods=["POST"])
def accept_friend():
    user_id = session.get("user_id")
    data = request.get_json()
    requester_id = data.get("user_id")

    friendship = Friendship.query.filter_by(user_id=requester_id, friend_id=user_id, status="pending").first()
    if not friendship:
        return jsonify({"error": "Friend request not found"}), 404

    friendship.status = "accepted"
    db.session.commit()
    return jsonify({"success": "Friend request accepted"}), 200


# -------------------------------
# DECLINE FRIEND REQUEST
# -------------------------------
@main_bp.route("/friends/decline", methods=["POST"])
def decline_friend():
    user_id = session.get("user_id")
    data = request.get_json()
    requester_id = data.get("user_id")

    friendship = Friendship.query.filter_by(user_id=requester_id, friend_id=user_id, status="pending").first()
    if not friendship:
        return jsonify({"error": "Friend request not found"}), 404

    db.session.delete(friendship)
    db.session.commit()
    return jsonify({"success": "Friend request declined"}), 200