from flask import Flask
from routes.main import main_bp, login_manager
from models import db

app = Flask(__name__)
app.secret_key = "planit"

app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:root@localhost/planit_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "static/uploads"

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)

# Register blueprints
app.register_blueprint(main_bp)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)