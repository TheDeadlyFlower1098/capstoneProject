from flask import Flask, render_template

def create_app():
    app = Flask(__name__)

    # Register blueprints (routes)
    from routes.main import main_bp
    app.register_blueprint(main_bp)

    return app

app = create_app()

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(debug=True)

