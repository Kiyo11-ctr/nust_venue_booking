# ============================================================
#  FILE: database.py
#  PURPOSE: Sets up the database and creates all the tables.
#           Based on the ERD: User, Venue, Booking, Notification.
#  DATABASE: SQLite (a simple file-based database, no installation needed)
# ============================================================

import sqlite3

# This is the name of the database file that will be created
DATABASE = 'nust_venue.db'


def get_db():
    """Open a connection to the database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # This makes results come back as dictionaries
    return conn


def init_db():
    """Create all the tables in the database (only runs once)."""
    conn = get_db()
    cursor = conn.cursor()

    # ----------------------------------------------------------
    # TABLE: User
    # Stores everyone who can log in: staff, students, and admins
    # ----------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS User (
            user_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT    NOT NULL,
            last_name  TEXT    NOT NULL,
            email      TEXT    NOT NULL UNIQUE,
            nust_id    TEXT    NOT NULL UNIQUE,
            password   TEXT    NOT NULL,
            role       TEXT    NOT NULL CHECK(role IN ('staff', 'student', 'admin'))
        )
    ''')

    # ----------------------------------------------------------
    # TABLE: Venue
    # Stores all the rooms/halls that can be booked
    # ----------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Venue (
            venue_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT    NOT NULL,
            location     TEXT    NOT NULL,
            capacity     INTEGER NOT NULL,
            equipment    TEXT,           -- e.g. "Projector, Computers"
            is_available INTEGER DEFAULT 1  -- 1 = available, 0 = not available
        )
    ''')

    # ----------------------------------------------------------
    # TABLE: Booking
    # Stores every booking request made by users
    # ----------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Booking (
            booking_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL,
            venue_id     INTEGER NOT NULL,
            booking_date TEXT    NOT NULL,  -- Format: YYYY-MM-DD
            start_time   TEXT    NOT NULL,  -- Format: HH:MM
            end_time     TEXT    NOT NULL,  -- Format: HH:MM
            purpose      TEXT    NOT NULL,
            status       TEXT    DEFAULT 'pending'
                          CHECK(status IN ('pending', 'approved', 'rejected', 'cancelled')),
            created_at   TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (user_id)  REFERENCES User(user_id),
            FOREIGN KEY (venue_id) REFERENCES Venue(venue_id)
        )
    ''')

    # ----------------------------------------------------------
    # TABLE: Notification
    # Stores messages sent to users about their bookings
    # ----------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Notification (
            notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id      INTEGER NOT NULL,
            user_id         INTEGER NOT NULL,
            message         TEXT    NOT NULL,
            sent_at         TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (booking_id) REFERENCES Booking(booking_id),
            FOREIGN KEY (user_id)    REFERENCES User(user_id)
        )
    ''')

    # ----------------------------------------------------------
    # Add some sample data so the system has something to show
    # ----------------------------------------------------------
    cursor.execute("SELECT COUNT(*) FROM Venue")
    if cursor.fetchone()[0] == 0:
        sample_venues = [
            ('Lecture Hall A', 'Block A, Ground Floor', 200, 'Projector', 1),
            ('Computer Lab 1', 'Block B, First Floor',  50,  'Computers', 1),
            ('Seminar Room 3', 'Block C, Second Floor', 30,  'Whiteboard, Projector', 1),
            ('Boardroom',      'Admin Block',           20,  'TV Screen', 1),
        ]
        cursor.executemany(
            "INSERT INTO Venue (name, location, capacity, equipment, is_available) VALUES (?,?,?,?,?)",
            sample_venues
        )

    # Add a default admin account so you can log in right away
    cursor.execute("SELECT COUNT(*) FROM User WHERE role='admin'")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO User (first_name, last_name, email, nust_id, password, role)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('Admin', 'NUST', 'admin@nust.na', 'ADMIN001', 'admin123', 'admin'))

    conn.commit()
    conn.close()
    print("✅ Database ready.")
