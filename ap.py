from flask import Flask
from models import db
from main import main_bp

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:cset155@localhost/planit_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "super-secret-key"

db.init_app(app)

with app.app_context():
    db.create_all()  # creates tables if they don't exist

app.register_blueprint(main_bp)

if __name__ == "__main__":
    app.run(debug=True)
