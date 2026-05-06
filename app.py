from flask import Flask
from extensions import db, login_manager

from models import User

from routes.main import main_bp
from routes.auth import auth_bp
from routes.tasks import task_bp
from routes.friends import friend_bp
from routes.events import event_bp
from routes.api import api_bp
from routes.budget import budget_bp
from routes.settings import settings_bp

from models import User

def create_app():
    app = Flask(__name__)

    # config (moved from run.py)
    app.secret_key = "planit"
    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:cset155@localhost/planit_db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = "static/uploads"

    # init extensions
    db.init_app(app)
    login_manager.init_app(app)

    # user loader
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(task_bp)
    app.register_blueprint(friend_bp)
    app.register_blueprint(event_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(budget_bp)
    app.register_blueprint(settings_bp)

    # create tables
    with app.app_context():
        db.create_all()

    return app