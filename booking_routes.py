# ============================================================
#  FILE: routes/booking_routes.py
#  PURPOSE: Handles everything to do with bookings.
#           Staff and students can make, view, edit, and cancel bookings.
#
#  ENDPOINTS:
#    POST   /bookings           - Request a new booking
#    GET    /bookings           - See your own bookings
#    PUT    /bookings/<id>      - Modify a pending booking
#    DELETE /bookings/<id>      - Cancel a booking
# ============================================================

from flask import Blueprint, request, jsonify, session
from database import get_db

booking_bp = Blueprint('booking', __name__)


def login_required():
    return session.get('user_id') is None


def check_double_booking(db, venue_id, booking_date, start_time, end_time, exclude_booking_id=None):
    """
    Checks if the venue is already booked at the requested time.
    Returns True if there IS a conflict (double booking).
    """
    query = '''
        SELECT booking_id FROM Booking
        WHERE venue_id     = ?
          AND booking_date = ?
          AND status       = 'approved'
          AND start_time   < ?
          AND end_time     > ?
    '''
    params = [venue_id, booking_date, end_time, start_time]

    # When modifying a booking, ignore the booking itself
    if exclude_booking_id:
        query += ' AND booking_id != ?'
        params.append(exclude_booking_id)

    conflict = db.execute(query, params).fetchone()
    return conflict is not None


def add_notification(db, user_id, booking_id, message):
    """Save a notification message for the user."""
    db.execute('''
        INSERT INTO Notification (user_id, booking_id, message)
        VALUES (?, ?, ?)
    ''', (user_id, booking_id, message))


# ---- REQUEST A NEW BOOKING ----
@booking_bp.route('/bookings', methods=['POST'])
def create_booking():
    """
    Expects JSON body:
    {
        "venue_id":     1,
        "booking_date": "2025-09-10",
        "start_time":   "09:00",
        "end_time":     "11:00",
        "purpose":      "Group study session"
    }
    """
    if login_required():
        return jsonify({'error': 'Please log in first'}), 401

    data    = request.get_json()
    user_id = session['user_id']

    # Validate required fields
    required = ['venue_id', 'booking_date', 'start_time', 'end_time', 'purpose']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'Missing field: {field}'}), 400

    # Make sure end time is after start time
    if data['start_time'] >= data['end_time']:
        return jsonify({'error': 'End time must be after start time'}), 400

    db = get_db()

    # Make sure the venue exists and is available
    venue = db.execute(
        'SELECT * FROM Venue WHERE venue_id = ? AND is_available = 1',
        (data['venue_id'],)
    ).fetchone()

    if not venue:
        db.close()
        return jsonify({'error': 'Venue not found or not available'}), 404

    # Check for double booking conflicts
    if check_double_booking(db, data['venue_id'], data['booking_date'],
                             data['start_time'], data['end_time']):
        db.close()
        return jsonify({'error': 'This venue is already booked at that time'}), 409

    # Create the booking (status starts as "pending" until admin approves)
    cursor = db.execute('''
        INSERT INTO Booking (user_id, venue_id, booking_date, start_time, end_time, purpose)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        data['venue_id'],
        data['booking_date'],
        data['start_time'],
        data['end_time'],
        data['purpose']
    ))

    booking_id = cursor.lastrowid

    # Send a notification to the user
    add_notification(db, user_id, booking_id,
                     f"Your booking for {venue['name']} on {data['booking_date']} is pending approval.")

    db.commit()
    db.close()

    return jsonify({'message': 'Booking request submitted! Waiting for admin approval.',
                    'booking_id': booking_id}), 201


# ---- VIEW YOUR OWN BOOKINGS ----
@booking_bp.route('/bookings', methods=['GET'])
def get_my_bookings():
    """Returns all bookings made by the currently logged-in user."""
    if login_required():
        return jsonify({'error': 'Please log in first'}), 401

    user_id = session['user_id']
    db      = get_db()

    bookings = db.execute('''
        SELECT
            b.booking_id,
            b.booking_date,
            b.start_time,
            b.end_time,
            b.purpose,
            b.status,
            b.created_at,
            v.name     AS venue_name,
            v.location AS venue_location
        FROM Booking b
        JOIN Venue v ON b.venue_id = v.venue_id
        WHERE b.user_id = ?
        ORDER BY b.booking_date DESC
    ''', (user_id,)).fetchall()

    db.close()
    return jsonify([dict(b) for b in bookings]), 200


# ---- MODIFY A PENDING BOOKING ----
@booking_bp.route('/bookings/<int:booking_id>', methods=['PUT'])
def update_booking(booking_id):
    """
    Allows the user to change their own pending booking.
    Expects JSON body with any of:
    {
        "booking_date": "2025-09-15",
        "start_time":   "10:00",
        "end_time":     "12:00",
        "purpose":      "Lecture"
    }
    """
    if login_required():
        return jsonify({'error': 'Please log in first'}), 401

    user_id = session['user_id']
    data    = request.get_json()
    db      = get_db()

    # Find the booking and make sure it belongs to this user
    booking = db.execute(
        'SELECT * FROM Booking WHERE booking_id = ? AND user_id = ?',
        (booking_id, user_id)
    ).fetchone()

    if not booking:
        db.close()
        return jsonify({'error': 'Booking not found'}), 404

    # Can only modify bookings that are still pending
    if booking['status'] != 'pending':
        db.close()
        return jsonify({'error': 'Only pending bookings can be modified'}), 400

    # Use existing values if new ones are not provided
    new_date  = data.get('booking_date', booking['booking_date'])
    new_start = data.get('start_time',   booking['start_time'])
    new_end   = data.get('end_time',     booking['end_time'])
    new_purp  = data.get('purpose',      booking['purpose'])

    if new_start >= new_end:
        db.close()
        return jsonify({'error': 'End time must be after start time'}), 400

    # Check for conflicts (excluding this booking itself)
    if check_double_booking(db, booking['venue_id'], new_date, new_start, new_end, booking_id):
        db.close()
        return jsonify({'error': 'This venue is already booked at that time'}), 409

    db.execute('''
        UPDATE Booking
        SET booking_date = ?, start_time = ?, end_time = ?, purpose = ?
        WHERE booking_id = ?
    ''', (new_date, new_start, new_end, new_purp, booking_id))

    db.commit()
    db.close()
    return jsonify({'message': 'Booking updated successfully'}), 200


# ---- CANCEL A BOOKING ----
@booking_bp.route('/bookings/<int:booking_id>', methods=['DELETE'])
def cancel_booking(booking_id):
    """Allows a user to cancel their own booking."""
    if login_required():
        return jsonify({'error': 'Please log in first'}), 401

    user_id = session['user_id']
    db      = get_db()

    booking = db.execute(
        'SELECT * FROM Booking WHERE booking_id = ? AND user_id = ?',
        (booking_id, user_id)
    ).fetchone()

    if not booking:
        db.close()
        return jsonify({'error': 'Booking not found'}), 404

    if booking['status'] == 'cancelled':
        db.close()
        return jsonify({'error': 'Booking is already cancelled'}), 400

    db.execute(
        "UPDATE Booking SET status = 'cancelled' WHERE booking_id = ?",
        (booking_id,)
    )

    add_notification(db, user_id, booking_id, 'Your booking has been cancelled.')

    db.commit()
    db.close()
    return jsonify({'message': 'Booking cancelled successfully'}), 200
