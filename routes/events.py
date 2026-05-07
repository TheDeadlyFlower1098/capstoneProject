from flask import Blueprint, request, jsonify, render_template, redirect
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import or_

from models import db, Event, EventInvite, User, Friendship

event_bp = Blueprint("events", __name__)

@event_bp.route("/events/new")
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

    return render_template("create_event.html", selected_date=today, friends=friends)


@event_bp.route("/events/new", methods=["POST"])
@login_required
def create_event():
    data = request.get_json() or request.form

    event_date = datetime.strptime(data["date"], "%Y-%m-%d").date()

    end_date = None
    if data.get("end_date"):
        end_date = datetime.strptime(data["end_date"], "%Y-%m-%d").date()

    all_day = data.get("all_day") in [True, "true", "on"]

    start_time = end_time = None
    if not all_day:
        start_time = datetime.strptime(data["start_time"], "%H:%M").time()
        end_time = datetime.strptime(data["end_time"], "%H:%M").time()

    reminder = data.get("reminder")
    reminder = None if reminder in ["", None, "none"] else int(reminder)

    event = Event(
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
        reminder_minutes_before=reminder
    )

    db.session.add(event)
    db.session.flush()

    for fid in data.get("invites", []):
        db.session.add(EventInvite(
            event_id=event.id,
            invited_user_id=int(fid),
            status="pending"
        ))

    db.session.commit()

    return jsonify({"success": True, "event_id": event.id})


@event_bp.route("/events/<int:event_id>/respond", methods=["POST"])
@login_required
def respond_to_invite(event_id):
    invite = EventInvite.query.filter_by(
        event_id=event_id,
        invited_user_id=current_user.id
    ).first_or_404()

    invite.status = request.form.get("response")
    db.session.commit()

    return redirect("/calendar")