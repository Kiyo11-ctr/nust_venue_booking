# ============================================================
#  FILE: routes/auth_routes.py
#  PURPOSE: Handles everything to do with users logging in
#           and registering new accounts.
#
#  ENDPOINTS:
#    POST /register  - Create a new account
#    POST /login     - Log in and get a session token
#    POST /logout    - Log out
# ============================================================

from flask import Blueprint, request, jsonify, session
from database import get_db

# A blueprint is just a group of related routes
auth_bp = Blueprint('auth', __name__)


# ---- REGISTER: Create a new user account ----
@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Expects JSON body:
    {
        "first_name": "John",
        "last_name":  "Doe",
        "email":      "john.doe@nust.na",
        "nust_id":    "220012345",
        "password":   "mypassword",
        "role":       "staff"   (or "student")
    }
    """
    data = request.get_json()

    # Make sure all required fields are present
    required = ['first_name', 'last_name', 'email', 'nust_id', 'password', 'role']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'Missing field: {field}'}), 400

    # Only staff and students can register. Admins are added manually.
    if data['role'] not in ('staff', 'student'):
        return jsonify({'error': 'Role must be either staff or student'}), 400

    db = get_db()
    try:
        db.execute('''
            INSERT INTO User (first_name, last_name, email, nust_id, password, role)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data['first_name'],
            data['last_name'],
            data['email'],
            data['nust_id'],
            data['password'],   # NOTE: In a real app, use hashing e.g. bcrypt
            data['role']
        ))
        db.commit()
        return jsonify({'message': 'Account created successfully!'}), 201

    except Exception as e:
        # This usually means the email or nust_id is already taken
        return jsonify({'error': 'Email or NUST ID already exists'}), 409

    finally:
        db.close()


# ---- LOGIN: Check credentials and start a session ----
@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Expects JSON body:
    {
        "nust_id":  "220012345",
        "password": "mypassword"
    }
    """
    data = request.get_json()

    if not data.get('nust_id') or not data.get('password'):
        return jsonify({'error': 'Please provide nust_id and password'}), 400

    db = get_db()
    user = db.execute(
        'SELECT * FROM User WHERE nust_id = ? AND password = ?',
        (data['nust_id'], data['password'])
    ).fetchone()
    db.close()

    if not user:
        return jsonify({'error': 'Incorrect NUST ID or password'}), 401

    # Save the user's info in the session (like a login cookie)
    session['user_id'] = user['user_id']
    session['role']    = user['role']
    session['name']    = user['first_name']

    return jsonify({
        'message': f"Welcome, {user['first_name']}!",
        'role':    user['role'],
        'user_id': user['user_id']
    }), 200


# ---- LOGOUT: End the session ----
@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200
