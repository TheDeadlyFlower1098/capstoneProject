from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user

from models import db, Task

task_bp = Blueprint("tasks", __name__)

@task_bp.route("/tasks")
@login_required
def tasks():
    user_tasks = Task.query.filter_by(user_id=current_user.id).all()

    list_names = sorted(list(set(task.list_name for task in user_tasks)))

    selected_list = request.args.get("list_name")
    if not selected_list and list_names:
        selected_list = list_names[0]
    elif not selected_list:
        selected_list = "New List"

    display_tasks = [t for t in user_tasks if t.list_name == selected_list]

    return render_template(
        "tasks.html",
        active_page="tasks",
        list_names=list_names,
        selected_list=selected_list,
        tasks=display_tasks
    )


@task_bp.route("/tasks/toggle/<int:task_id>", methods=["POST"])
@login_required
def toggle_task(task_id):
    task = Task.query.get_or_404(task_id)

    if task.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    task.is_completed = data.get("is_completed", False)

    db.session.commit()
    return jsonify({"success": True})


@task_bp.route("/tasks/add", methods=["POST"])
@login_required
def add_task():
    data = request.get_json()

    new_task = Task(
        task_name=data.get("task_name"),
        list_name=data.get("list_name"),
        is_completed=False,
        user_id=current_user.id
    )

    db.session.add(new_task)
    db.session.commit()

    return jsonify({
        "success": True,
        "task_id": new_task.id,
        "task_name": new_task.task_name
    })


@task_bp.route("/tasks/new-list", methods=["POST"])
@login_required
def create_list():
    new_task = Task(
        list_name="New List Title",
        task_name="Default List Item",
        is_completed=False,
        user_id=current_user.id
    )

    db.session.add(new_task)
    db.session.commit()

    return jsonify({"success": True, "list_name": "New List Title"})


@task_bp.route("/tasks/rename-list", methods=["POST"])
@login_required
def rename_list():
    data = request.get_json()

    tasks = Task.query.filter_by(
        user_id=current_user.id,
        list_name=data.get("old_name")
    ).all()

    for t in tasks:
        t.list_name = data.get("new_name")

    db.session.commit()
    return jsonify({"success": True})


@task_bp.route("/tasks/rename-task/<int:task_id>", methods=["POST"])
@login_required
def rename_task(task_id):
    task = Task.query.get_or_404(task_id)

    if task.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    task.task_name = data.get("task_name")

    db.session.commit()
    return jsonify({"success": True})


@task_bp.route("/tasks/delete/<int:task_id>", methods=["POST"])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)

    if task.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    db.session.delete(task)
    db.session.commit()
    return jsonify({"success": True})


@task_bp.route("/tasks/delete-list", methods=["POST"])
@login_required
def delete_list():
    data = request.get_json()

    Task.query.filter_by(
        user_id=current_user.id,
        list_name=data.get("list_name")
    ).delete()

    db.session.commit()
    return jsonify({"success": True})