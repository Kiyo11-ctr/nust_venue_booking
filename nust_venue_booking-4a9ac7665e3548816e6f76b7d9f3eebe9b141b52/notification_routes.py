# ============================================================
#  FILE: routes/notification_routes.py  (optional extra file)
#  PURPOSE: Lets users see their own notifications.
#
#  ENDPOINT:
#    GET /notifications  - See all your notifications
# ============================================================
# NOTE: This is already included in admin_routes.py for admins.
#       Add this blueprint to app.py if you want users to also
#       be able to check their notifications.
#
#   In app.py, add:
#       from routes.notification_routes import notification_bp
#       app.register_blueprint(notification_bp)
# ============================================================

from flask import Blueprint, jsonify, session
from database import get_db

notification_bp = Blueprint('notification', __name__)


@notification_bp.route('/notifications', methods=['GET'])
def get_my_notifications():
    """Returns all notifications for the currently logged-in user."""
    if not session.get('user_id'):
        return jsonify({'error': 'Please log in first'}), 401

    user_id = session['user_id']
    db      = get_db()

    notes = db.execute('''
        SELECT n.notification_id, n.message, n.sent_at,
               b.booking_date, v.name AS venue_name
        FROM Notification n
        JOIN Booking b ON n.booking_id = b.booking_id
        JOIN Venue   v ON b.venue_id   = v.venue_id
        WHERE n.user_id = ?
        ORDER BY n.sent_at DESC
    ''', (user_id,)).fetchall()

    db.close()
    return jsonify([dict(n) for n in notes]), 200
