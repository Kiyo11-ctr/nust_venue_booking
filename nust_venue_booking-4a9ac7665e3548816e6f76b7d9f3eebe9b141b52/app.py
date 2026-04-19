# ============================================================
#  FILE: app.py
#  PURPOSE: This is the main file that starts the backend server.
#           Run this file to start the whole system.
#  HOW TO RUN: python app.py
# ============================================================

from flask import Flask
from database import init_db
from auth_routes import auth_bp
from venue_routes import venue_bp
from booking_routes import booking_bp
from admin_routes import admin_bp

app = Flask(__name__)

app.config['SECRET_KEY'] = 'nust-venue-secret-key-2025'

app.register_blueprint(auth_bp)
app.register_blueprint(venue_bp)
app.register_blueprint(booking_bp)
app.register_blueprint(admin_bp)

@app.route("/")
def home():
    return "NUST Venue Booking System Backend is running."

if __name__ == "__main__":
    init_db()
    app.run(debug=True)