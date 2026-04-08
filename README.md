# ============================================================
#  NUST Venue Booking System - Backend
#  Department of Software Engineering
# ============================================================

## What this is
A simple backend (server-side code) for the NUST Venue Booking System.
Built with Python (Flask) and SQLite.

---

## Folder Structure

```
nust_venue_booking/
│
├── app.py                          ← START HERE — runs the server
├── database.py                     ← Sets up the database and sample data
├── requirements.txt                ← Packages to install
│
└── routes/
    ├── auth_routes.py              ← Login and Register
    ├── venue_routes.py             ← Browse/filter venues
    ├── booking_routes.py           ← Make/view/edit/cancel bookings
    ├── admin_routes.py             ← Admin panel (approve, manage venues)
    └── notification_routes.py      ← View your notifications (optional)
```

---

## How to Set Up and Run

### Step 1 — Make sure Python is installed
Open your terminal/command prompt and type:
```
python --version
```
You should see something like `Python 3.10.x`

### Step 2 — Install the required package
```
pip install -r requirements.txt
```

### Step 3 — Start the server
```
python app.py
```
You should see:
```
✅ Database ready.
 * Running on http://127.0.0.1:5000
```

---

## How to Test (using a browser or Postman)

### Default Admin Account
- NUST ID:  `ADMIN001`
- Password: `admin123`

### Sample Venues (added automatically)
- Lecture Hall A — Capacity 200, Equipment: Projector
- Computer Lab 1 — Capacity 50,  Equipment: Computers
- Seminar Room 3 — Capacity 30,  Equipment: Whiteboard, Projector
- Boardroom       — Capacity 20,  Equipment: TV Screen

---

## All API Endpoints

### Authentication
| Method | URL          | Description              |
|--------|--------------|--------------------------|
| POST   | /register    | Create a new account     |
| POST   | /login       | Log in                   |
| POST   | /logout      | Log out                  |

### Venues (logged-in users)
| Method | URL                   | Description                      |
|--------|-----------------------|----------------------------------|
| GET    | /venues               | See all available venues         |
| GET    | /venues?capacity=50   | Filter by minimum capacity       |
| GET    | /venues?equipment=PC  | Filter by equipment              |
| GET    | /venues/1             | See details of venue #1          |

### Bookings (logged-in users)
| Method | URL               | Description                    |
|--------|-------------------|--------------------------------|
| POST   | /bookings         | Request a new booking          |
| GET    | /bookings         | See your own bookings          |
| PUT    | /bookings/1       | Modify booking #1              |
| DELETE | /bookings/1       | Cancel booking #1              |

### Admin Only
| Method | URL                    | Description                    |
|--------|------------------------|--------------------------------|
| GET    | /admin/bookings        | See all bookings               |
| GET    | /admin/bookings?status=pending | Filter by status       |
| PUT    | /admin/bookings/1      | Approve/reject booking #1      |
| GET    | /admin/venues          | See all venues                 |
| POST   | /admin/venues          | Add a new venue                |
| PUT    | /admin/venues/1        | Update venue #1                |
| DELETE | /admin/venues/1        | Delete venue #1                |
| GET    | /admin/notifications   | See all notifications          |

---

## Example Requests (copy into Postman)

**Register:**
```json
POST /register
{
    "first_name": "Jane",
    "last_name":  "Smith",
    "email":      "jane.smith@nust.na",
    "nust_id":    "220054321",
    "password":   "password123",
    "role":       "staff"
}
```

**Login:**
```json
POST /login
{
    "nust_id":  "220054321",
    "password": "password123"
}
```

**Book a Venue:**
```json
POST /bookings
{
    "venue_id":     1,
    "booking_date": "2025-09-10",
    "start_time":   "09:00",
    "end_time":     "11:00",
    "purpose":      "Group study session"
}
```

**Approve a Booking (admin):**
```json
PUT /admin/bookings/1
{
    "action": "approve"
}
```
