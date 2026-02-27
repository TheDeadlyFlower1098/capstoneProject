from flask import Blueprint, render_template, session, request, flash, redirect, url_for, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Task, Transaction, Friendship, Event, EventInvite
from datetime import datetime
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

@main_bp.route("/update-budget", methods=["POST"])
@login_required
def update_budget():
    new_saved = request.form.get('saved_amount')
    new_limit = request.form.get('limit_amount')

    last_tx = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    
    current_limit = float(new_limit) if new_limit else (last_tx.budget_limit if last_tx else 0)
    current_saved = float(new_saved) if new_saved else float(current_user.balance)

    difference = current_saved - float(current_user.balance)
    current_user.balance = current_saved
    
    if difference != 0:
        new_transaction = Transaction(
            amount=difference,
            budget_limit=current_limit,
            updated_total=current_saved,
            user_id=current_user.id,
            transaction_date=datetime.now().strftime("%Y-%m-%d")
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


# ---------------- Events ---------------- #
@main_bp.route("/events/new")
def new_event_page():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("main.login"))

    date = request.args.get("date")

    friends = User.query.join(
        Friendship,
        ((Friendship.friend_id == User.id) & (Friendship.user_id == user_id)) |
        ((Friendship.user_id == User.id) & (Friendship.friend_id == user_id))
    ).filter(Friendship.status == "accepted").all()

    return render_template(
        "create_event.html",
        selected_date=date,
        friends=friends,
        active_page="calendar"
    )


# -------------------------------
# NEW EVENTS 
# -------------------------------
@main_bp.route("/events/new", methods=["POST"])
def create_event_form():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "You must be logged in."})

    try:
        # Parse start date
        event_date_str = request.form.get("date")
        if not event_date_str:
            return jsonify({"error": "Start date is required."})
        event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()

        # Parse optional end date
        end_date_str = request.form.get("end_date")
        end_date = None
        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            if end_date < event_date:
                return jsonify({"error": "End date cannot be before start date."})

        # All-day checkbox
        all_day = bool(request.form.get("all_day"))

        start_time = None
        end_time = None
        if not all_day:
            start_time_str = request.form.get("start_time")
            end_time_str = request.form.get("end_time")
            if start_time_str and end_time_str:
                start_time = datetime.strptime(start_time_str, "%H:%M").time()
                end_time = datetime.strptime(end_time_str, "%H:%M").time()
                if end_time <= start_time:
                    return jsonify({"error": "End time must be after start time."})
            elif start_time_str or end_time_str:
                # Only one time filled
                return jsonify({"error": "Both start and end time must be filled if not all-day."})

        # Create event
        new_event = Event(
            creator_id=user_id,
            title=request.form["title"],
            description=request.form.get("description"),
            location=request.form.get("location"),
            event_date=event_date,
            end_date=end_date,
            start_time=start_time,
            end_time=end_time,
            all_day=all_day,
            color=request.form.get("color", "blue"),
            is_private=bool(request.form.get("is_private"))
        )

        db.session.add(new_event)
        db.session.commit()

        # handle invites
        invite_ids = request.form.getlist("invites")
        for friend_id in invite_ids:
            invite = EventInvite(event_id=new_event.id, invited_user_id=int(friend_id))
            db.session.add(invite)
        db.session.commit()

        return jsonify({"success": True, "event_id": new_event.id})

    except Exception as e:
        return jsonify({"error": str(e)})


# -------------------------------
# ACCEPT/DECLINE INVITES
# -------------------------------
@main_bp.route("/events/<int:event_id>/respond", methods=["POST"])
def respond_to_invite(event_id):
    user_id = session.get("user_id")

    invite = EventInvite.query.filter_by(
        event_id=event_id,
        invited_user_id=user_id
    ).first_or_404()

    response = request.form.get("response")
    if response in ["accepted", "declined"]:
        invite.status = response
        db.session.commit()

    return redirect("/calendar")


# -------------------------------
# GET EVENTS (for calendar)
# -------------------------------
@main_bp.route("/api/events")
def get_events():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify([])

    events = Event.query.outerjoin(EventInvite).filter(
        (Event.creator_id == user_id) |
        (EventInvite.invited_user_id == user_id)
    ).order_by(Event.event_date, Event.start_time).distinct().all()

    formatted = []
    for e in events:
        accepted = []
        pending = []
        for invite in e.invites:
            invite_data = {
                "id": invite.user.id,
                "name": f"{invite.user.first_name} {invite.user.last_name}",
                "profile_pic": invite.user.profile_pic,
                "status": invite.status
            }
            if invite.status == "accepted":
                accepted.append(invite_data)
            elif invite.status == "pending":
                pending.append(invite_data)

        formatted.append({
            "id": e.id,
            "title": e.title,
            "description": e.description,
            "location": e.location,
            "date": e.event_date.strftime("%Y-%m-%d"),
            "end_date": e.end_date.strftime("%Y-%m-%d") if e.end_date else None,
            "start_time": None if e.all_day else (e.start_time.strftime("%H:%M") if e.start_time else None),
            "end_time": None if e.all_day else (e.end_time.strftime("%H:%M") if e.end_time else None),
            "all_day": e.all_day,
            "color": e.color,
            "accepted_users": accepted,
            "pending_users": pending
        })

    return jsonify(formatted)


# ---------------- Edit Event Page ---------------- #
@main_bp.route("/events/<int:event_id>/edit")
def edit_event_page(event_id):
    user_id = session.get("user_id")
    event = Event.query.get_or_404(event_id)

    if event.creator_id != user_id:
        return "Unauthorized", 403

    return render_template("edit_event.html", event=event)


# ---------------- Edit Events ---------------- #
@main_bp.route("/events/<int:event_id>/edit", methods=["POST"])
def edit_event(event_id):
    user_id = session.get("user_id")
    event = Event.query.get_or_404(event_id)

    if event.creator_id != user_id:
        return "Unauthorized", 403

    event.title = request.form["title"]
    event.description = request.form.get("description")
    event.location = request.form.get("location")
    event.color = request.form.get("color")
    event.repeat_type = request.form.get("repeat_type")
    event.is_private = bool(request.form.get("is_private"))

    db.session.commit()

    return redirect("/calendar")