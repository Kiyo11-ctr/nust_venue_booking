# ============================================================
#  FILE: routes/admin_routes.py
#  PURPOSE: Handles admin-only actions.
#           Admins can approve/reject bookings and manage venues.
#
#  ENDPOINTS:
#    GET    /admin/bookings          - See ALL bookings
#    PUT    /admin/bookings/<id>     - Approve or reject a booking
#    GET    /admin/venues            - See all venues (including unavailable)
#    POST   /admin/venues            - Add a new venue
#    PUT    /admin/venues/<id>       - Update venue details
#    DELETE /admin/venues/<id>       - Remove a venue
# ============================================================

from flask import Blueprint, request, jsonify, session
from database import get_db

admin_bp = Blueprint('admin', __name__)


def admin_required():
    """Check that the person logged in is an admin."""
    return session.get('role') != 'admin'


def add_notification(db, user_id, booking_id, message):
    """Save a notification for the user."""
    db.execute('''
        INSERT INTO Notification (user_id, booking_id, message)
        VALUES (?, ?, ?)
    ''', (user_id, booking_id, message))


# ---- VIEW ALL BOOKINGS (admin sees everything) ----
@admin_bp.route('/admin/bookings', methods=['GET'])
def get_all_bookings():
    """Returns every booking in the system with user and venue details."""
    if admin_required():
        return jsonify({'error': 'Admin access required'}), 403

    # Optional filter by status: /admin/bookings?status=pending
    status_filter = request.args.get('status', '')

    db    = get_db()
    query = '''
        SELECT
            b.booking_id,
            b.booking_date,
            b.start_time,
            b.end_time,
            b.purpose,
            b.status,
            b.created_at,
            v.name       AS venue_name,
            v.location   AS venue_location,
            u.first_name AS user_first_name,
            u.last_name  AS user_last_name,
            u.email      AS user_email,
            u.nust_id    AS user_nust_id
        FROM Booking b
        JOIN Venue v ON b.venue_id = v.venue_id
        JOIN User  u ON b.user_id  = u.user_id
    '''
    params = []
    if status_filter:
        query += ' WHERE b.status = ?'
        params.append(status_filter)

    query += ' ORDER BY b.booking_date DESC'

    bookings = db.execute(query, params).fetchall()
    db.close()
    return jsonify([dict(b) for b in bookings]), 200


# ---- APPROVE OR REJECT A BOOKING ----
@admin_bp.route('/admin/bookings/<int:booking_id>', methods=['PUT'])
def update_booking_status(booking_id):
    """
    Admin approves or rejects a booking.
    Expects JSON body:
    {
        "action": "approve"   (or "reject" or "cancel")
    }
    """
    if admin_required():
        return jsonify({'error': 'Admin access required'}), 403

    data   = request.get_json()
    action = data.get('action', '').lower()

    if action not in ('approve', 'reject', 'cancel'):
        return jsonify({'error': 'Action must be: approve, reject, or cancel'}), 400

    db = get_db()

    booking = db.execute('SELECT * FROM Booking WHERE booking_id = ?', (booking_id,)).fetchone()
    if not booking:
        db.close()
        return jsonify({'error': 'Booking not found'}), 404

    # Map action word to database status value
    status_map = {
        'approve': 'approved',
        'reject':  'rejected',
        'cancel':  'cancelled'
    }
    new_status = status_map[action]

    db.execute(
        'UPDATE Booking SET status = ? WHERE booking_id = ?',
        (new_status, booking_id)
    )

    # Get venue name for the notification message
    venue = db.execute('SELECT name FROM Venue WHERE venue_id = ?', (booking['venue_id'],)).fetchone()

    message_map = {
        'approved':  f"Your booking for {venue['name']} on {booking['booking_date']} has been APPROVED.",
        'rejected':  f"Your booking for {venue['name']} on {booking['booking_date']} has been REJECTED.",
        'cancelled': f"Your booking for {venue['name']} on {booking['booking_date']} has been CANCELLED by admin."
    }
    add_notification(db, booking['user_id'], booking_id, message_map[new_status])

    db.commit()
    db.close()
    return jsonify({'message': f'Booking has been {new_status}.'}), 200


# ========================================================
#  VENUE MANAGEMENT (Admin only)
# ========================================================

# ---- VIEW ALL VENUES ----
@admin_bp.route('/admin/venues', methods=['GET'])
def admin_get_venues():
    """Admin can see all venues, including ones marked as unavailable."""
    if admin_required():
        return jsonify({'error': 'Admin access required'}), 403

    db     = get_db()
    venues = db.execute('SELECT * FROM Venue').fetchall()
    db.close()
    return jsonify([dict(v) for v in venues]), 200


# ---- ADD A NEW VENUE ----
@admin_bp.route('/admin/venues', methods=['POST'])
def add_venue():
    """
    Admin adds a new venue.
    Expects JSON body:
    {
        "name":      "Lecture Hall B",
        "location":  "Block D, Ground Floor",
        "capacity":  150,
        "equipment": "Projector, Sound System"
    }
    """
    if admin_required():
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()

    required = ['name', 'location', 'capacity']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'Missing field: {field}'}), 400

    db = get_db()
    db.execute('''
        INSERT INTO Venue (name, location, capacity, equipment, is_available)
        VALUES (?, ?, ?, ?, 1)
    ''', (data['name'], data['location'], data['capacity'], data.get('equipment', '')))

    db.commit()
    db.close()
    return jsonify({'message': f"Venue '{data['name']}' added successfully."}), 201


# ---- UPDATE A VENUE ----
@admin_bp.route('/admin/venues/<int:venue_id>', methods=['PUT'])
def update_venue(venue_id):
    """
    Admin updates venue details.
    Expects JSON body with any of:
    {
        "name":         "New Hall Name",
        "location":     "Block E",
        "capacity":     200,
        "equipment":    "Projector",
        "is_available": 0    (0 = closed, 1 = open)
    }
    """
    if admin_required():
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()
    db   = get_db()

    venue = db.execute('SELECT * FROM Venue WHERE venue_id = ?', (venue_id,)).fetchone()
    if not venue:
        db.close()
        return jsonify({'error': 'Venue not found'}), 404

    # Only update the fields that were provided; keep the rest the same
    new_name      = data.get('name',         venue['name'])
    new_location  = data.get('location',     venue['location'])
    new_capacity  = data.get('capacity',     venue['capacity'])
    new_equipment = data.get('equipment',    venue['equipment'])
    new_available = data.get('is_available', venue['is_available'])

    db.execute('''
        UPDATE Venue
        SET name = ?, location = ?, capacity = ?, equipment = ?, is_available = ?
        WHERE venue_id = ?
    ''', (new_name, new_location, new_capacity, new_equipment, new_available, venue_id))

    db.commit()
    db.close()
    return jsonify({'message': 'Venue updated successfully'}), 200


# ---- DELETE (REMOVE) A VENUE ----
@admin_bp.route('/admin/venues/<int:venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    """Admin removes a venue from the system."""
    if admin_required():
        return jsonify({'error': 'Admin access required'}), 403

    db    = get_db()
    venue = db.execute('SELECT * FROM Venue WHERE venue_id = ?', (venue_id,)).fetchone()

    if not venue:
        db.close()
        return jsonify({'error': 'Venue not found'}), 404

    db.execute('DELETE FROM Venue WHERE venue_id = ?', (venue_id,))
    db.commit()
    db.close()
    return jsonify({'message': f"Venue '{venue['name']}' deleted."}), 200


# ---- VIEW NOTIFICATIONS (all users get notified) ----
@admin_bp.route('/admin/notifications', methods=['GET'])
def get_all_notifications():
    """Admin can see all notifications sent in the system."""
    if admin_required():
        return jsonify({'error': 'Admin access required'}), 403

    db    = get_db()
    notes = db.execute('''
        SELECT n.*, u.first_name, u.last_name
        FROM Notification n
        JOIN User u ON n.user_id = u.user_id
        ORDER BY n.sent_at DESC
    ''').fetchall()
    db.close()
    return jsonify([dict(n) for n in notes]), 200
