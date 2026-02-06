from flask import Flask, render_template
from routes.main import app

if __name__ == "__main__":
    app.run(debug=True)