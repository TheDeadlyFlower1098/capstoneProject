from flask import Flask
from routes.main import main_bp, db, setup_login # Added setup_login here

app = Flask(__name__)
# Flask-Login REQUIRES a secret key to handle user sessions
app.secret_key = "planit" 

app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:root@localhost/planit_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# 1. Initialize DB
db.init_app(app)

# 2. Initialize Login Manager (THIS IS THE FIX)
setup_login(app)

# 3. Register Blueprints
app.register_blueprint(main_bp)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)