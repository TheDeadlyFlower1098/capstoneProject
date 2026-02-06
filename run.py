from flask import Flask
from routes.main import main_bp, db

def create_app():
    app = Flask(__name__)

    # Needed for session usage
    app.secret_key = "dev-secret-change-later"

    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:cset155@localhost/planit_db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
