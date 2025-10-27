const express = require('express');
const path = require('path');
const nodemailer = require('nodemailer');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.static('public'));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.get('/signin', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'signin.html'));
});

// Demo request endpoint
app.post('/api/demo-request', (req, res) => {
    const { name, email, university, role, message } = req.body;
    
    // In a real implementation, you would:
    // 1. Save to database
    // 2. Send email notification
    // 3. Add to CRM
    
    console.log('Demo request received:', { name, email, university, role, message });
    
    res.json({ 
        success: true, 
        message: 'Thank you for your interest! We\'ll be in touch soon.' 
    });
});

// Waitlist signup endpoint
app.post('/api/waitlist', (req, res) => {
    const { email, interests } = req.body;
    
    console.log('Waitlist signup:', { email, interests });
    
    res.json({ 
        success: true, 
        message: 'You\'ve been added to our waitlist!' 
    });
});

// Sign in endpoint (placeholder)
app.post('/api/signin', (req, res) => {
    const { email, password, dataLink } = req.body;
    
    // In a real implementation, you would:
    // 1. Validate credentials
    // 2. Check data link format
    // 3. Authenticate user
    
    console.log('Sign in attempt:', { email, dataLink });
    
    res.json({ 
        success: true, 
        message: 'Sign in successful! Redirecting to dashboard...' 
    });
});

app.listen(PORT, () => {
    console.log(`UDiscovery landing page running on http://localhost:${PORT}`);
});
