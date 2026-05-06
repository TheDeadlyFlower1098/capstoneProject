from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime

from models import db, Transaction

budget_bp = Blueprint("budget", __name__)

@budget_bp.route("/budget")
@login_required
def budget():
    last = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    tx = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).all()

    return render_template("budget.html", last_transaction=last, transactions=tx)


@budget_bp.route("/update-budget", methods=["POST"])
@login_required
def update_budget():
    new_saved = request.form.get("saved_amount")
    new_limit = request.form.get("limit_amount")
    new_goal = request.form.get("goal_amount")
    note = request.form.get("transaction_note")

    last_tx = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()

    current_limit = float(new_limit) if new_limit else (last_tx.budget_limit if last_tx else 0)
    current_saved = float(new_saved) if new_saved else float(current_user.balance)

    if new_goal:
        current_user.goal = float(new_goal)

    diff = current_saved - float(current_user.balance)
    current_user.balance = current_saved

    if diff != 0:
        db.session.add(Transaction(
            amount=diff,
            budget_limit=current_limit,
            updated_total=current_saved,
            user_id=current_user.id,
            transaction_date=datetime.now(),
            category=note if note else "General"
        ))
        flash("Transaction recorded!", "success")

    elif last_tx and new_limit and float(new_limit) != last_tx.budget_limit:
        last_tx.budget_limit = current_limit
        flash("Budget updated!", "info")

    db.session.commit()
    return redirect(url_for("budget.budget"))