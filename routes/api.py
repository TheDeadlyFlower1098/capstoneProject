from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from models import db, Event, EventInvite, User

api_bp = Blueprint("api", __name__)

@api_bp.route("/api/status")
@login_required
def user_status():
    if request.args.get("share", "true") == "false":
        return jsonify({"status": "hidden"})

    return jsonify({"status": "online", "last_active": "Today"})


@api_bp.route("/api/events")
@login_required
def api_events():
    events = (
        db.session.query(Event, User)
        .join(User, User.id == Event.creator_id)
        .outerjoin(EventInvite,
            (EventInvite.event_id == Event.id) &
            (EventInvite.invited_user_id == current_user.id))
        .filter(
            (Event.creator_id == current_user.id) |
            (EventInvite.status == "accepted") |
            (Event.visibility == "friends")
        )
        .distinct()
        .all()
    )

    result = []

    for e, creator in events:
        attendees = db.session.query(User).join(EventInvite).filter(
            EventInvite.event_id == e.id,
            EventInvite.status == "accepted"
        ).all()

        result.append({
            "id": e.id,
            "name": e.title,
            "creator": f"{creator.first_name} {creator.last_name}",
            "attendees": [f"{u.first_name} {u.last_name}" for u in attendees],
            "start_date": e.start_date.strftime("%Y-%m-%d"),
            "end_date": e.end_date.strftime("%Y-%m-%d") if e.end_date else None,
            "start_time": e.start_time.strftime("%H:%M") if e.start_time else None,
            "end_time": e.end_time.strftime("%H:%M") if e.end_time else None,
            "all_day": e.all_day,
            "repeat_type": e.repeat_type,
            "color": e.color,
            "visibility": e.visibility,
            "reminder": e.reminder_minutes_before
        })

    return jsonify(result)