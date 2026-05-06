from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os

from models import db

settings_bp = Blueprint("settings", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@settings_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        file = request.files.get("profile_pic")

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            folder = os.path.join(current_app.root_path, "static", "uploads")
            os.makedirs(folder, exist_ok=True)

            file.save(os.path.join(folder, filename))

            current_user.profile_pic = filename
            db.session.commit()

            flash("Profile updated!", "success")
        else:
            flash("Invalid file", "danger")

        return redirect(url_for("settings.settings"))

    return render_template("settings.html", active_page="settings")