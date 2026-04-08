# ============================================================
#  FILE: routes/venue_routes.py
#  PURPOSE: Handles browsing and filtering of venues.
#           This is what users see on the "Venues Page".
#
#  ENDPOINTS:
#    GET  /venues              - See all available venues
#    GET  /venues?capacity=50  - Filter venues by minimum capacity
#    GET  /venues?equipment=Projector  - Filter by equipment
#    GET  /venues/<id>         - See details of one venue
# ============================================================

from flask import Blueprint, request, jsonify, session
from database import get_db

venue_bp = Blueprint('venue', __name__)


def login_required():
    """A simple helper to check if the user is logged in."""
    return session.get('user_id') is None


# ---- GET ALL VENUES (with optional filters) ----
@venue_bp.route('/venues', methods=['GET'])
def get_venues():
    """
    Returns a list of available venues.
    You can add filters in the URL:
      /venues?capacity=100
      /venues?equipment=Projector
      /venues?capacity=50&equipment=Computers
    """
    if login_required():
        return jsonify({'error': 'Please log in first'}), 401

    # Read optional filter values from the URL
    min_capacity = request.args.get('capacity', type=int)
    equipment    = request.args.get('equipment', '')

    db = get_db()

    # Start with a basic query for available venues
    query  = 'SELECT * FROM Venue WHERE is_available = 1'
    params = []

    # Add capacity filter if provided
    if min_capacity:
        query += ' AND capacity >= ?'
        params.append(min_capacity)

    # Add equipment filter if provided
    if equipment:
        query += ' AND equipment LIKE ?'
        params.append(f'%{equipment}%')

    venues = db.execute(query, params).fetchall()
    db.close()

    # Convert the results to a list of plain dictionaries
    result = [dict(v) for v in venues]
    return jsonify(result), 200


# ---- GET A SINGLE VENUE BY ID ----
@venue_bp.route('/venues/<int:venue_id>', methods=['GET'])
def get_venue(venue_id):
    """Returns the details of one specific venue."""
    if login_required():
        return jsonify({'error': 'Please log in first'}), 401

    db = get_db()
    venue = db.execute('SELECT * FROM Venue WHERE venue_id = ?', (venue_id,)).fetchone()
    db.close()

    if not venue:
        return jsonify({'error': 'Venue not found'}), 404

    return jsonify(dict(venue)), 200
