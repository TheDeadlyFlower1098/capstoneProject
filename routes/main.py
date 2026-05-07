from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Task, Event

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def home():
    if current_user.is_authenticated:
        return render_template("homeLoggedIn.html", active_page="home")
    return render_template("home.html")


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


@main_bp.route("/calendar")
def calendar():
    return render_template("calendar.html", active_page="calendar")