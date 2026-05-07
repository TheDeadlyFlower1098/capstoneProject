from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user

from models import db, User, Friendship, EventInvite, Event

friend_bp = Blueprint("friends", __name__)

@friend_bp.route("/friends")
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
        fid = f.friend_id if f.user_id == user.id else f.user_id
        friend = User.query.get(fid)

        friends_list.append({
            "id": friend.id,
            "name": f"{friend.first_name} {friend.last_name}",
            "profile_pic": friend.profile_pic,
            "user_code": friend.user_code,
            "last_active": "Today"
        })

    pending = Friendship.query.filter_by(friend_id=user.id, status="pending").all()

    requests_list = []
    for r in pending:
        u = User.query.get(r.user_id)
        requests_list.append({
            "id": u.id,
            "name": f"{u.first_name} {u.last_name}",
            "profile_pic": u.profile_pic,
            "user_code": u.user_code
        })

    invites = EventInvite.query.filter_by(invited_user_id=user.id, status="pending").all()

    invites_list = []
    for i in invites:
        event = Event.query.get(i.event_id)
        creator = User.query.get(event.creator_id)

        invites_list.append({
            "event_id": event.id,
            "title": event.title,
            "date": event.start_date.strftime("%Y-%m-%d"),
            "location": event.location,
            "creator": f"{creator.first_name} {creator.last_name}",
            "creator_pic": creator.profile_pic
        })

    return render_template(
        "friends.html",
        user_code=user.user_code,
        friends_list=friends_list,
        requests_list=requests_list,
        invites_list=invites_list
    )


@friend_bp.route("/friends/add", methods=["POST"])
@login_required
def add_friend():
    data = request.get_json()

    friend = User.query.filter_by(user_code=data.get("code")).first()

    if not friend or friend.id == current_user.id:
        return jsonify({"error": "Invalid friend code"}), 404

    existing = Friendship.query.filter(
        ((Friendship.user_id == current_user.id) &
         (Friendship.friend_id == friend.id)) |
        ((Friendship.user_id == friend.id) &
         (Friendship.friend_id == current_user.id))
    ).first()

    if existing:
        return jsonify({"error": "Friendship already exists"}), 400

    db.session.add(Friendship(
        user_id=current_user.id,
        friend_id=friend.id,
        status="pending"
    ))
    db.session.commit()

    return jsonify({"success": "Friend request sent"})


@friend_bp.route("/friends/accept", methods=["POST"])
@login_required
def accept_friend():
    data = request.get_json()

    f = Friendship.query.filter_by(
        user_id=data.get("user_id"),
        friend_id=current_user.id,
        status="pending"
    ).first()

    f.status = "accepted"
    db.session.commit()

    return jsonify({"success": True})


@friend_bp.route("/friends/decline", methods=["POST"])
@login_required
def decline_friend():
    data = request.get_json()

    f = Friendship.query.filter_by(
        user_id=data.get("user_id"),
        friend_id=current_user.id,
        status="pending"
    ).first()

    db.session.delete(f)
    db.session.commit()

    return jsonify({"success": True})