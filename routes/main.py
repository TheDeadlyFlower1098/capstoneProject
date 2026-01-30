from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def home():
    return render_template("home.html")

@main_bp.route("/upcoming")
def upcoming_events():
    return render_template("upcoming.html", active_page="upcoming")


@main_bp.route("/friends")
def friends():
    return render_template("friends.html", active_page="friends")


@main_bp.route("/budget")
def budget():
    return render_template("budget.html", active_page="budget")


@main_bp.route("/calendar")
def calendar():
    return render_template("calendar.html", active_page="calendar")



@main_bp.route("/newTasks")
def todo_list():
    return render_template("newTasks.html", active_page="newTasks")


@main_bp.route("/settings")
def settings():
    return render_template("settings.html", active_page="settings")