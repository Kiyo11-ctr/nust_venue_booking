const express = require('express');
const sql = require('mssql');
const cors = require('cors');
const bodyParser = require('body-parser');

const app = express();
const PORT = 5000;

// Middleware
app.use(cors());
app.use(bodyParser.json());

// SQL Server configuration (Update with your SQL Server details)
const dbConfig = {
    user: 'your_username',        // Replace with your SQL username
    password: 'your_password',    // Replace with your SQL password
    server: 'localhost',          // e.g., 'localhost' or 'DESKTOP-XXX'
    database: 'NUST_Venue_Booking',
    options: {
        encrypt: false,           // For local development
        trustServerCertificate: true
    }
};

// Connect to database
sql.connect(dbConfig).then(() => {
    console.log('Connected to SQL Server');
}).catch(err => {
    console.error('Database connection failed:', err);
});

// ==================== AUTHENTICATION ====================

// Login endpoint
app.post('/api/auth/login', async (req, res) => {
    const { username, password } = req.body;
    try {
        const result = await sql.query`
            SELECT user_id, username, role 
            FROM Users 
            WHERE username = ${username} AND password_hash = ${password}
        `;
        
        if (result.recordset.length === 0) {
            return res.status(401).json({ error: 'Invalid credentials' });
        }
        
        const user = result.recordset[0];
        res.json({ 
            userId: user.user_id, 
            username: user.username, 
            role: user.role 
        });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Register endpoint
app.post('/api/auth/register', async (req, res) => {
    const { username, password, role } = req.body;
    
    if (!['student', 'staff'].includes(role)) {
        return res.status(400).json({ error: 'Invalid role' });
    }
    
    try {
        await sql.query`
            INSERT INTO Users (username, password_hash, role)
            VALUES (${username}, ${password}, ${role})
        `;
        res.json({ message: 'User registered successfully' });
    } catch (err) {
        if (err.number === 2627) { // Duplicate key error
            res.status(400).json({ error: 'Username already exists' });
        } else {
            res.status(500).json({ error: err.message });
        }
    }
});

// ==================== VENUES ====================

// Get all venues (with optional filters)
app.get('/api/venues', async (req, res) => {
    const { minCapacity, equipment } = req.query;
    
    let query = 'SELECT * FROM Venues WHERE is_available = 1';
    
    if (minCapacity) {
        query += ` AND capacity >= ${parseInt(minCapacity)}`;
    }
    if (equipment && equipment !== '') {
        query += ` AND equipment LIKE '%${equipment}%'`;
    }
    
    try {
        const result = await sql.query(query);
        res.json(result.recordset);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Update venue (admin only)
app.put('/api/venues/:id', async (req, res) => {
    const { id } = req.params;
    const { name, capacity, equipment } = req.body;
    
    try {
        await sql.query`
            UPDATE Venues 
            SET name = ${name}, capacity = ${capacity}, equipment = ${equipment}
            WHERE venue_id = ${id}
        `;
        res.json({ message: 'Venue updated successfully' });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// ==================== BOOKINGS ====================

// Get bookings for a specific user
app.get('/api/bookings/user/:userId', async (req, res) => {
    const { userId } = req.params;
    
    try {
        const result = await sql.query`
            SELECT b.*, v.name as venue_name 
            FROM Bookings b
            JOIN Venues v ON b.venue_id = v.venue_id
            WHERE b.user_id = ${userId}
            ORDER BY b.booking_date DESC, b.start_time
        `;
        res.json(result.recordset);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Get all bookings (admin only)
app.get('/api/bookings/all', async (req, res) => {
    try {
        const result = await sql.query`
            SELECT b.*, v.name as venue_name, u.username 
            FROM Bookings b
            JOIN Venues v ON b.venue_id = v.venue_id
            JOIN Users u ON b.user_id = u.user_id
            ORDER BY b.booking_date DESC, b.start_time
        `;
        res.json(result.recordset);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Create new booking
app.post('/api/bookings', async (req, res) => {
    const { userId, venueId, date, startTime, endTime, purpose } = req.body;
    
    try {
        // Check for overlapping bookings
        const conflict = await sql.query`
            SELECT * FROM Bookings 
            WHERE venue_id = ${venueId} 
            AND booking_date = ${date}
            AND status IN ('pending', 'approved')
            AND (
                (start_time < ${endTime} AND end_time > ${startTime})
            )
        `;
        
        if (conflict.recordset.length > 0) {
            return res.status(409).json({ error: 'Time slot already booked' });
        }
        
        await sql.query`
            INSERT INTO Bookings (user_id, venue_id, booking_date, start_time, end_time, purpose, status)
            VALUES (${userId}, ${venueId}, ${date}, ${startTime}, ${endTime}, ${purpose}, 'pending')
        `;
        res.json({ message: 'Booking created successfully' });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Update booking status (admin only)
app.put('/api/bookings/:id/status', async (req, res) => {
    const { id } = req.params;
    const { status } = req.body;
    
    try {
        await sql.query`
            UPDATE Bookings 
            SET status = ${status}
            WHERE booking_id = ${id}
        `;
        res.json({ message: 'Booking status updated' });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Update booking (user edit)
app.put('/api/bookings/:id', async (req, res) => {
    const { id } = req.params;
    const { date, startTime, endTime, purpose } = req.body;
    
    try {
        await sql.query`
            UPDATE Bookings 
            SET booking_date = ${date}, start_time = ${startTime}, 
                end_time = ${endTime}, purpose = ${purpose}
            WHERE booking_id = ${id} AND status = 'pending'
        `;
        res.json({ message: 'Booking updated successfully' });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Delete booking (user cancel)
app.delete('/api/bookings/:id', async (req, res) => {
    const { id } = req.params;
    
    try {
        await sql.query`DELETE FROM Bookings WHERE booking_id = ${id}`;
        res.json({ message: 'Booking cancelled' });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Start server
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});
