from flask import Flask
from models import db
from routes.main import main_bp, login_manager

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:cset155@localhost/planit_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "super-secret-key"

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

# Register blueprint
app.register_blueprint(main_bp)

if __name__ == "__main__":
    app.run(debug=True)