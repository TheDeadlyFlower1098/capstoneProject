from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from sqlalchemy import or_
import os

from models import EventInvite, db, User, Transaction, Friendship, Event, Task

# ------------------- CONFIG -------------------
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

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
        return render_template("dashboard.html", active_page="home")
    return render_template("dashboard.html")

@main_bp.route("/dashboard")
@login_required
def dashboard():
    from datetime import date

    tasks = Task.query.filter_by(user_id=current_user.id).all()

    completed = sum(1 for t in tasks if t.is_completed)
    total = len(tasks)

    progress = int((completed / total) * 100) if total > 0 else 0

    # TODAY
    today = date.today()

    # UPCOMING EVENTS (after today)
    upcoming_events = Event.query.filter(Event.start_date > today).all()

    return render_template(
        "dashboard.html",
        tasks=tasks,
        completed=completed,
        total=total,
        progress=progress,
        upcoming=upcoming_events   
    )


@main_bp.route("/budget")
@login_required
def budget():
    # Get the most recent transaction to show current budget/limit
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).all()

    return render_template("budget.html", active_page="budget", last_transaction=last_transaction, transactions=transactions)

@main_bp.route("/update-budget", methods=["POST"])
@login_required
def update_budget():
    new_saved = request.form.get('saved_amount')
    new_limit = request.form.get('limit_amount')
    new_goal = request.form.get('goal_amount')
    transaction_note = request.form.get('transaction_note') # 1. Grab the note from the form

    last_tx = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    
    current_limit = float(new_limit) if new_limit else (last_tx.budget_limit if last_tx else 0)
    current_saved = float(new_saved) if new_saved else float(current_user.balance)

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
            transaction_date=datetime.now(),
            category=transaction_note if transaction_note else 'General' # 2. Save the note or default to 'General'
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
@login_required
def tasks():
    # 1. Get all tasks for the current user
    user_tasks = Task.query.filter_by(user_id=current_user.id).all()

    # 2. Get unique list names for the dropdown
    # We use a set to avoid duplicates, then sort them
    list_names = sorted(list(set(task.list_name for task in user_tasks)))

    # 3. Determine which list to display
    # Default to the first list if it exists, otherwise "Default List"
    selected_list = request.args.get('list_name')
    if not selected_list and list_names:
        selected_list = list_names[0]
    elif not selected_list:
        selected_list = "New List"

    # 4. Filter tasks for the currently selected list
    display_tasks = [t for t in user_tasks if t.list_name == selected_list]

    return render_template(
        "tasks.html", 
        active_page="tasks", 
        list_names=list_names, 
        selected_list=selected_list,
        tasks=display_tasks
    )

# Add to main.py
@main_bp.route("/tasks/toggle/<int:task_id>", methods=["POST"])
@login_required
def toggle_task(task_id):
    # Retrieve the task or return 404
    task = Task.query.get_or_404(task_id)

    # Security Check: Ensure the task belongs to the logged-in user
    if task.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    # Update the boolean status
    task.is_completed = data.get("is_completed", False)
    
    try:
        db.session.commit()
        return jsonify({"success": True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
# Add to main.py
@main_bp.route("/tasks/add", methods=["POST"])
@login_required
def add_task():
    data = request.get_json()
    task_name = data.get("task_name")
    list_name = data.get("list_name")

    if not task_name or not list_name:
        return jsonify({"error": "Missing task name or list name"}), 400

    new_task = Task(
        task_name=task_name,
        list_name=list_name,
        is_completed=False,
        user_id=current_user.id
    )

    try:
        db.session.add(new_task)
        db.session.commit()
        return jsonify({
            "success": True, 
            "task_id": new_task.id,
            "task_name": new_task.task_name
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@main_bp.route("/tasks/new-list", methods=["POST"])
@login_required
def create_list():
    # Placeholder values as requested
    new_list_name = "New List Title"
    
    new_task = Task(
        list_name=new_list_name,
        task_name="Default List Item",
        is_completed=False,
        user_id=current_user.id
    )

    try:
        db.session.add(new_task)
        db.session.commit()
        # Return the name so the frontend can redirect to it
        return jsonify({"success": True, "list_name": new_list_name}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# --- Add these to main.py ---

@main_bp.route("/tasks/rename-list", methods=["POST"])
@login_required
def rename_list():
    data = request.get_json()
    old_name = data.get("old_name")
    new_name = data.get("new_name")

    if not new_name or old_name == new_name:
        return jsonify({"success": False}), 400

    # Offensive Security Check: Ensure we only update the current user's lists
    tasks = Task.query.filter_by(user_id=current_user.id, list_name=old_name).all()
    
    try:
        for task in tasks:
            task.list_name = new_name
        db.session.commit()
        return jsonify({"success": True, "new_name": new_name})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@main_bp.route("/tasks/rename-task/<int:task_id>", methods=["POST"])
@login_required
def rename_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    # IDOR Security Check: Ensure the user owns this specific task
    if task.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    new_name = data.get("task_name")

    if not new_name:
        return jsonify({"error": "Task name cannot be empty"}), 400

    try:
        task.task_name = new_name
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@main_bp.route("/tasks/delete/<int:task_id>", methods=["POST"])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)

    # Security Check: Prevent IDOR (Insecure Direct Object Reference)
    if task.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        db.session.delete(task)
        db.session.commit()
        return jsonify({"success": True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@main_bp.route("/tasks/delete-list", methods=["POST"])
@login_required
def delete_list():
    data = request.get_json()
    list_name = data.get("list_name")

    if not list_name:
        return jsonify({"error": "No list name provided"}), 400

    # Delete all tasks belonging to this list for the current user
    try:
        Task.query.filter_by(user_id=current_user.id, list_name=list_name).delete()
        db.session.commit()
        return jsonify({"success": True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

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

        if file and file.filename != "":
            import os
            import uuid
            from flask import current_app
            from werkzeug.utils import secure_filename

            filename = secure_filename(file.filename)
            filename = str(uuid.uuid4()) + "_" + filename

            upload_folder = os.path.join(current_app.root_path, "static/uploads")
            filepath = os.path.join(upload_folder, filename)

            file.save(filepath)

            # store ONLY filename in DB
            current_user.profile_pic = filename
            db.session.commit()

            flash("Profile picture updated!", "success")

        return redirect(url_for("main.settings"))

    return render_template(
        "settings.html",
        active_page="settings",
        user_name=f"{current_user.first_name} {current_user.last_name}"
    )

@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if not user:
            flash("Email not registered.", "error")
            return render_template("login.html")

        if not check_password_hash(user.password, password):
            flash("Incorrect password.", "error")
            return render_template("login.html")

        login_user(user)
        return redirect(url_for("main.dashboard"))

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

# --- UNFRIEND AND BLOCK ---
# --- UNFRIEND ---
@main_bp.route("/unfriend/<int:user_id>", methods=["POST"])
@login_required
def unfriend(user_id):
    user_id_self = current_user.id

    friendship = Friend.query.filter_by(
        user_id=user_id_self,
        friend_id=user_id
    ).first()

    if friendship:
        db.session.delete(friendship)

    # optional: remove reverse friendship too
    reverse = Friend.query.filter_by(
        user_id=user_id,
        friend_id=user_id_self
    ).first()

    if reverse:
        db.session.delete(reverse)

    db.session.commit()

    return jsonify({"success": True})


# --- BLOCK USER ---
@main_bp.route("/block/<int:user_id>", methods=["POST"])
@login_required
def block_user(user_id):
    user_id_self = current_user.id

    # remove friendship if exists
    Friend.query.filter_by(user_id=user_id_self, friend_id=user_id).delete()
    Friend.query.filter_by(user_id=user_id, friend_id=user_id_self).delete()

    # add to blocked table (you must have this model)
    block = Block(user_id=user_id_self, blocked_id=user_id)
    db.session.add(block)

    db.session.commit()

    return jsonify({"success": True})

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

    # ===============================
    # CURRENT FRIENDS
    # ===============================
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

    # --- Pending friend requests ---
    pending_requests = Friendship.query.filter_by(
        friend_id=user.id, status="pending"
    ).all()

    requests_list = []
    for r in pending_requests:
        requester = User.query.get(r.user_id)
        if not requester:
            continue
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


# -------------------------------
# USER STATUS API
# -------------------------------
@main_bp.route("/api/status")
@login_required
def user_status():

    settings = request.args.get("share", "true")

    if settings == "false":
        return jsonify({"status": "hidden"})

    return jsonify({
        "status": "online",
        "last_active": "Today"
    })

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
            visibility=data.get("visibility", "private"),
            reminder_minutes_before = data.get("reminder_minutes_before", 10)
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

    events = (
        db.session.query(Event, User)
        .join(User, User.id == Event.creator_id)
        .outerjoin(
            EventInvite,
            (EventInvite.event_id == Event.id) &
            (EventInvite.invited_user_id == current_user.id)
        )
        .filter(
            (Event.creator_id == current_user.id) |
            (EventInvite.status == "accepted") |
            (Event.visibility == "friends")
        )
        .distinct()
        .all()
    )

    data = []

    for e, creator in events:

        is_creator = e.creator_id == current_user.id

        accepted_invites = (
            db.session.query(User)
            .join(EventInvite, EventInvite.invited_user_id == User.id)
            .filter(
                EventInvite.event_id == e.id,
                EventInvite.status == "accepted"
            )
            .all()
        )

        attendees = [
            f"{u.first_name} {u.last_name}"
            for u in accepted_invites
        ]

        event_data = {
            "id": e.id,
            "name": e.title,
            "title": e.title,
            "creator": f"{creator.first_name} {creator.last_name}",
            "attendees": attendees,
            "location": e.location,
            "start_date": e.start_date.strftime("%Y-%m-%d"),
            "end_date": e.end_date.strftime("%Y-%m-%d") if e.end_date else None,
            "start_time": e.start_time.strftime("%H:%M") if e.start_time else None,
            "end_time": e.end_time.strftime("%H:%M") if e.end_time else None,
            "all_day": e.all_day,
            "repeat_type": e.repeat_type,
            "color": e.color,
            "visibility": e.visibility
        }

        if not is_creator and e.visibility == "private":
            event_data["location"] = None

        data.append(event_data)

    return jsonify(data)
