from flask import Blueprint, render_template, session, request, flash, redirect, url_for, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Task, Transaction, Friendship, Event, EventInvite
from datetime import datetime
from sqlalchemy import or_, and_

main_bp = Blueprint("main", __name__)
login_manager = LoginManager()
login_manager.login_view = "main.login"

def setup_login(app):
    login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------------- HOME -------------------
@main_bp.route("/")
def home():
    if current_user.is_authenticated:
        return render_template("homeLoggedIn.html", active_page="home")
    return render_template("home.html")

@main_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", active_page="dashboard")

# ------------------- BUDGET -------------------
@main_bp.route("/budget")
@login_required
def budget():
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).all()
    return render_template("budget.html", active_page="budget", last_transaction=last_transaction, transactions=transactions)

@main_bp.route("/update-budget", methods=["POST"])
@login_required
def update_budget():
    try:
        new_saved = request.form.get('saved_amount')
        new_limit = request.form.get('limit_amount')

        last_tx = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
        current_limit = float(new_limit) if new_limit else (last_tx.budget_limit if last_tx else 0)
        current_saved = float(new_saved) if new_saved else float(current_user.balance)

        difference = current_saved - float(current_user.balance)
        current_user.balance = current_saved

        if difference != 0:
            new_tx = Transaction(
                amount=difference,
                budget_limit=current_limit,
                updated_total=current_saved,
                user_id=current_user.id,
                transaction_date=datetime.now().strftime("%Y-%m-%d")
            )
            db.session.add(new_tx)
            flash(f"Transaction of ${abs(difference):.2f} recorded!", "success")
        elif last_tx and new_limit and float(new_limit) != last_tx.budget_limit:
            last_tx.budget_limit = current_limit
            flash("Budget limit updated!", "info")

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating budget: {e}", "danger")

    return redirect(url_for("main.budget"))

@main_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    if first_name := request.form.get('first_name'):
        current_user.first_name = first_name
    if balance := request.form.get('balance'):
        current_user.balance = float(balance)
    db.session.commit()
    flash("Profile updated.", "success")
    return redirect(url_for('main.dashboard'))

# ------------------- TASKS -------------------
@main_bp.route("/tasks")
@login_required
def tasks():
    return render_template("tasks.html", active_page="tasks")

# ------------------- SETTINGS -------------------
@main_bp.route("/settings")
@login_required
def settings():
    return render_template("settings.html", active_page="settings")

# ------------------- AUTH -------------------
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
        db.session.commit()
        flash("Registered successfully! You can now log in.", "success")
        return redirect(url_for("main.login"))
    return render_template("register.html")

@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form.get("email")).first()
        if user and check_password_hash(user.password, request.form.get("password")):
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for("main.home"))
        flash("Invalid credentials.", "danger")
    return render_template("login.html")

@main_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "logout")
    return redirect(url_for("main.home"))

# ------------------- FRIENDS -------------------
@main_bp.route("/friends")
@login_required
def friends():
    user = current_user
    friendships = Friendship.query.filter(
        or_(Friendship.user_id==user.id, Friendship.friend_id==user.id),
        Friendship.status=="accepted"
    ).all()
    friends_list = []
    for f in friendships:
        friend_id = f.friend_id if f.user_id == user.id else f.user_id
        friend = User.query.get(friend_id)
        if not friend: continue
        friends_list.append({
            "id": friend.id,
            "name": f"{friend.first_name} {friend.last_name}",
            "profile_pic": friend.profile_pic,
            "user_code": friend.user_code
        })
    return render_template("friends.html", user_code=user.user_code, friends_list=friends_list, requests_list=[])

@main_bp.route("/friends/add", methods=["POST"])
@login_required
def add_friend():
    data = request.get_json()
    code = data.get("code","").strip()
    if not code: return jsonify({"error": "No friend code provided"}), 400

    friend = User.query.filter_by(user_code=code).first()
    if not friend or friend.id == current_user.id:
        return jsonify({"error": "Invalid friend code"}), 400

    existing = Friendship.query.filter(
        or_(
            and_(Friendship.user_id==current_user.id, Friendship.friend_id==friend.id),
            and_(Friendship.user_id==friend.id, Friendship.friend_id==current_user.id)
        )
    ).first()
    if existing:
        return jsonify({"error": "Friendship already exists"}), 400

    db.session.add(Friendship(user_id=current_user.id, friend_id=friend.id, status="pending"))
    db.session.commit()
    return jsonify({"success": f"Friend request sent to {friend.first_name}"}), 200

@main_bp.route("/friends/accept", methods=["POST"])
@login_required
def accept_friend():
    data = request.get_json()
    requester_id = data.get("user_id")
    friendship = Friendship.query.filter_by(user_id=requester_id, friend_id=current_user.id, status="pending").first()
    if not friendship: return jsonify({"error": "Request not found"}), 404
    friendship.status = "accepted"
    db.session.commit()
    return jsonify({"success": "Friend request accepted"}), 200

@main_bp.route("/friends/decline", methods=["POST"])
@login_required
def decline_friend():
    data = request.get_json()
    requester_id = data.get("user_id")
    friendship = Friendship.query.filter_by(user_id=requester_id, friend_id=current_user.id, status="pending").first()
    if not friendship: return jsonify({"error": "Request not found"}), 404
    db.session.delete(friendship)
    db.session.commit()
    return jsonify({"success": "Friend request declined"}), 200

# ------------------- CALENDAR -------------------
@main_bp.route("/calendar")
@login_required
def calendar():
    return render_template("calendar.html", active_page="calendar")

# ------------------- EVENTS -------------------
@main_bp.route("/events/new")
@login_required
def new_event_page():
    user = current_user
    friends = User.query.join(
        Friendship,
        or_(
            and_(Friendship.user_id==user.id, Friendship.friend_id==User.id),
            and_(Friendship.friend_id==user.id, Friendship.user_id==User.id)
        )
    ).filter(Friendship.status=="accepted").all()
    date = request.args.get("date")
    return render_template("create_event.html", selected_date=date, friends=friends, active_page="calendar")

@main_bp.route("/events/new", methods=["POST"])
@login_required
def create_event_form():
    user_id = current_user.id
    try:
        title = request.form.get("title","").strip()
        if not title: return jsonify({"error":"Title required"}), 400

        event_date_str = request.form.get("date")
        event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date() if event_date_str else None
        if not event_date: return jsonify({"error":"Start date required"}), 400

        end_date = datetime.strptime(request.form["end_date"], "%Y-%m-%d").date() if request.form.get("end_date") else None
        if end_date and end_date < event_date:
            return jsonify({"error":"End date cannot be before start date"}), 400

        all_day = request.form.get("all_day")=="on"
        start_time = datetime.strptime(request.form["start_time"], "%H:%M").time() if request.form.get("start_time") else None
        end_time = datetime.strptime(request.form["end_time"], "%H:%M").time() if request.form.get("end_time") else None
        if start_time and end_time and end_time <= start_time:
            return jsonify({"error":"End time must be after start time"}), 400

        new_event = Event(
            creator_id=user_id,
            title=title,
            description=request.form.get("description"),
            location=request.form.get("location"),
            event_date=event_date,
            end_date=end_date,
            start_time=start_time,
            end_time=end_time,
            all_day=all_day,
            color=request.form.get("color","blue"),
            is_private=request.form.get("is_private")=="on"
        )
        db.session.add(new_event)
        db.session.flush()

        for friend_id in request.form.getlist("invites"):
            fid = int(friend_id)
            if fid == user_id: continue
            if not Friendship.query.filter(
                or_(and_(Friendship.user_id==user_id, Friendship.friend_id==fid),
                    and_(Friendship.user_id==fid, Friendship.friend_id==user_id)),
                Friendship.status=="accepted"
            ).first(): continue
            if EventInvite.query.filter_by(event_id=new_event.id, invited_user_id=fid).first(): continue
            db.session.add(EventInvite(event_id=new_event.id, invited_user_id=fid))

        db.session.commit()
        return jsonify({"success":True, "event_id":new_event.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error":"Error creating event"}),500

@main_bp.route("/events/<int:event_id>/edit")
@login_required
def edit_event_page(event_id):
    event = Event.query.get_or_404(event_id)
    if event.creator_id != current_user.id: return "Unauthorized",403
    return render_template("edit_event.html", event=event)

@main_bp.route("/events/<int:event_id>/edit", methods=["POST"])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.creator_id != current_user.id: return "Unauthorized",403

    event.title = request.form["title"]
    event.description = request.form.get("description")
    event.location = request.form.get("location")
    event.color = request.form.get("color")
    event.repeat_type = request.form.get("repeat_type")
    event.is_private = bool(request.form.get("is_private"))
    db.session.commit()
    flash("Event updated.", "success")
    return redirect(url_for("main.calendar"))

@main_bp.route("/events/<int:event_id>/respond", methods=["POST"])
@login_required
def respond_to_invite(event_id):
    invite = EventInvite.query.filter_by(event_id=event_id, invited_user_id=current_user.id).first_or_404()
    response = request.form.get("response")
    if response in ["accepted","declined"]:
        invite.status = response
        db.session.commit()
    return redirect(url_for("main.calendar"))

@main_bp.route("/api/events")
@login_required
def get_events():
    events = Event.query.outerjoin(EventInvite).filter(
        or_(Event.creator_id==current_user.id, EventInvite.invited_user_id==current_user.id)
    ).order_by(Event.event_date, Event.start_time).distinct().all()

    formatted = []
    for e in events:
        accepted, pending = [], []
        for i in e.invites:
            data = {"id":i.user.id,"name":f"{i.user.first_name} {i.user.last_name}","profile_pic":i.user.profile_pic,"status":i.status}
            if i.status=="accepted": accepted.append(data)
            elif i.status=="pending": pending.append(data)
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