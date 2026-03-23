from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from sqlalchemy import or_
import os
from flask import Response
from models import EventInvite, db, User, Transaction, Friendship, Event

# ------------------- CONFIG -------------------
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

# ------------------- LOGIN MANAGER -------------------
# ------------------- LOGIN MANAGER -------------------


login_manager = LoginManager()
login_manager.login_view = "main.login"

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ------------------- BLUEPRINT -------------------
main_bp = Blueprint("main", __name__)

# ------------------- HELPERS -------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# =====================================================
# ROUTES
# =====================================================
@main_bp.route("/")
def home():
    if current_user.is_authenticated:
        return render_template("homeLoggedIn.html", active_page="home")
    return render_template("home.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", active_page="dashboard")


@main_bp.route("/budget")
@login_required
def budget():
    # Get the most recent transaction to show current budget/limit
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).all()

    return render_template("budget.html", active_page="budget", last_transaction=last_transaction, transactions=transactions)

# In main.py
@main_bp.route("/update-budget", methods=["POST"])
@login_required
def update_budget():
    new_saved = request.form.get('saved_amount')
    new_limit = request.form.get('limit_amount')
    new_goal = request.form.get('goal_amount') # 1. Get the new goal from form

    last_tx = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    
    current_limit = float(new_limit) if new_limit else (last_tx.budget_limit if last_tx else 0)
    current_saved = float(new_saved) if new_saved else float(current_user.balance)

    # 2. Update the goal if provided
    if new_goal is not None:
        current_user.goal = float(new_goal)

    difference = current_saved - float(current_user.balance)
    current_user.balance = current_saved
    
    if difference != 0:
        new_transaction = Transaction(
            amount=difference,
            budget_limit=current_limit,
            updated_total=current_saved,
            user_id=current_user.id,
            transaction_date=datetime.now() # Use datetime object, SQLA handles formatting
        )
        db.session.add(new_transaction)
        flash(f"Transaction of ${abs(difference):.2f} recorded!", "success")
    
    elif last_tx and new_limit and float(new_limit) != last_tx.budget_limit:
        last_tx.budget_limit = current_limit
        flash("Budget limit updated!", "info")

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating budget: {e}", "danger")
        
    return redirect(url_for('main.budget'))
    
@main_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    new_balance = request.form.get('balance')
    new_first_name = request.form.get('first_name')

    if new_balance:
        current_user.balance = new_balance
        
    if new_first_name:
        current_user.first_name = new_first_name

    db.session.commit()
    return redirect(url_for('main.dashboard'))


@main_bp.route("/calendar")
def calendar():
    return render_template("calendar.html", active_page="calendar")


@main_bp.route("/tasks")
def tasks():
    return render_template("tasks.html", active_page="tasks")

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


@main_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        file = request.files.get("profile_pic")

        if file and file.filename:
            current_user.profile_pic = file.read()
            current_user.profile_pic_type = file.content_type

            db.session.commit()
            flash("Profile picture updated!", "success")

        return redirect(url_for("main.settings"))

    return render_template(
        "settings.html",
        active_page="settings",
        user_name=f"{current_user.first_name} {current_user.last_name}"
    )


@main_bp.route("/profile_pic/<int:user_id>")
def profile_pic(user_id):
    user = User.query.get_or_404(user_id)

    if not user.profile_pic:
        return redirect(url_for("static", filename="uploads/default.png"))

    return Response(
        user.profile_pic,
        mimetype=user.profile_pic_type
    )

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
@login_required
def send_friend_request():
    sender_id = current_user.id
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
    user_id = current_user.id
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
    user_id = current_user.id
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
    user_id = current_user.id
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
    user_id = current_user.id
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
    user_id = current_user.id
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

# --- INITIALIZE DATABASE ---


@main_bp.route("/logout")
def logout():
    logout_user() # This is the Flask-Login way
    flash("You have been logged out.", "logout")
    return redirect(url_for("main.home"))

# ---------------- FRIENDS ---------------- #
@main_bp.route("/friends")
@login_required
def friends():

    user = current_user

    friendships = Friendship.query.filter(
        ((Friendship.user_id == user.id) |
         (Friendship.friend_id == user.id)) &
        (Friendship.status == "accepted")
    ).all()

    friends_list = []

    for f in friendships:
        friend_id = f.friend_id if f.user_id == user.id else f.user_id
        friend = User.query.get(friend_id)

        if not friend:
            continue

        friends_list.append({
            "id": friend.id,
            "name": f"{friend.first_name} {friend.last_name}",
            "profile_pic": friend.profile_pic,
            "user_code": friend.user_code,
            "last_active": "Today"
        })

    return render_template(
        "friends.html",
        user_code=user.user_code,
        friends_list=friends_list,
        requests_list=[]
    )

# -------------------------------
# ADD FRIEND (SEND REQUEST)
# -------------------------------
@main_bp.route("/friends/add", methods=["POST"])
def add_friend():
    user_id = current_user.id
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
@login_required
def accept_friend():
    if not current_user.is_authenticated:
        return redirect(url_for("main.login"))

    user_id = current_user.id
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
@login_required
def decline_friend():
    if not current_user.is_authenticated:
        return redirect(url_for("main.login"))

    user_id = current_user.id
    data = request.get_json()
    requester_id = data.get("user_id")

    friendship = Friendship.query.filter_by(user_id=requester_id, friend_id=user_id, status="pending").first()
    if not friendship:
        return jsonify({"error": "Friend request not found"}), 404

    db.session.delete(friendship)
    db.session.commit()
    return jsonify({"success": "Friend request declined"}), 200


# =====================================================
# EVENTS
# =====================================================

# -------------------------------
# CREATE EVENT PAGE (GET)
# -------------------------------
@main_bp.route("/events/new")
@login_required
def create_event_page():
    today = datetime.now().strftime("%Y-%m-%d")

    friends = User.query.join(
        Friendship,
        or_(
            (Friendship.user_id == current_user.id) & (Friendship.friend_id == User.id),
            (Friendship.friend_id == current_user.id) & (Friendship.user_id == User.id)
        )
    ).filter(Friendship.status == "accepted").all()

    return render_template(
        "create_event.html",
        selected_date=today,
        friends=friends
    )


# -------------------------------
# CREATE EVENT (POST - AJAX)
# -------------------------------
@main_bp.route("/events/new", methods=["POST"])
@login_required
def create_event():
    try:
        data = request.get_json() or request.form

        # =========================
        # REQUIRED DATE
        # =========================
        date_str = data.get("date")
        if not date_str:
            return jsonify({"error": "Start date is required."}), 400

        event_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        # =========================
        # OPTIONAL END DATE
        # =========================
        end_date_str = data.get("end_date")
        end_date = None
        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            if end_date < event_date:
                return jsonify({"error": "End date cannot be before start date."}), 400

        # =========================
        # ALL DAY + TIME HANDLING
        # =========================
        all_day = data.get("all_day") in [True, "true", "on"]

        start_time = None
        end_time = None

        if not all_day:
            start_str = data.get("start_time")
            end_str = data.get("end_time")

            if not start_str or not end_str:
                return jsonify({"error": "Start and end times are required."}), 400

            start_time = datetime.strptime(start_str, "%H:%M").time()
            end_time = datetime.strptime(end_str, "%H:%M").time()

            if end_time <= start_time:
                return jsonify({"error": "End time must be after start time."}), 400

        # =========================
        # CREATE EVENT
        # =========================
        new_event = Event(
            creator_id=current_user.id,
            title=data.get("title"),
            description=data.get("description"),
            location=data.get("location"),
            start_date=event_date,
            end_date=end_date,
            start_time=start_time,
            end_time=end_time,
            all_day=all_day,
            color=data.get("color", "blue"),
            repeat_type=data.get("repeat_type"),
            visibility=data.get("visibility", "private")
        )

        db.session.add(new_event)
        db.session.flush()  # get event id before commit

        # =========================
        # HANDLE INVITES
        # =========================
        invite_ids = data.get("invites", [])
        for friend_id in invite_ids:
            invite = EventInvite(
                event_id=new_event.id,
                invited_user_id=int(friend_id),
                status="pending"
            )
            db.session.add(invite)

        db.session.commit()

        return jsonify({
            "success": True,
            "event_id": new_event.id
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
# -------------------------------
# RESPOND TO INVITE
# -------------------------------
@main_bp.route("/events/<int:event_id>/respond", methods=["POST"])
@login_required
def respond_to_invite(event_id):

    invite = EventInvite.query.filter_by(
        event_id=event_id,
        invited_user_id=current_user.id
    ).first_or_404()

    response = request.form.get("response")

    if response in ["accepted", "declined"]:
        invite.status = response
        db.session.commit()

    return redirect("/calendar")


# -------------------------------
# GET EVENTS (Calendar API)
# -------------------------------
@main_bp.route("/api/events")
@login_required
def api_events():
    events = Event.query.filter_by(creator_id=current_user.id).all()
    data = []
    for e in events:
        data.append({
            "id": e.id,
            "title": e.title,
            "name": e.title,          # Ensure JS can access .name
            "start_date": e.start_date.strftime("%Y-%m-%d"),
            "end_date": e.end_date.strftime("%Y-%m-%d") if e.end_date else None,
            "start_time": e.start_time.strftime("%H:%M") if e.start_time else None,
            "end_time": e.end_time.strftime("%H:%M") if e.end_time else None,
            "all_day": e.all_day,
            "repeat_type": e.repeat_type,
            "color": e.color,
            "visibility": e.visibility,
        })
    return jsonify(data)
