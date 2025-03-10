const express = require('express');
const path = require('path');
const app = express();
const PORT = process.env.PORT || 3000;

// Serve static files
app.use('/static', express.static(path.join(__dirname, 'static')));

// Routes
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'templates', 'index.html'));
});

app.get('/login', (req, res) => {
    res.sendFile(path.join(__dirname, 'templates', 'auth', 'login.html'));
});

app.get('/register', (req, res) => {
    res.sendFile(path.join(__dirname, 'templates', 'auth', 'register.html'));
});

app.get('/communities', (req, res) => {
    res.sendFile(path.join(__dirname, 'templates', 'communities', 'index.html'));
});

app.get('/messages', (req, res) => {
    res.sendFile(path.join(__dirname, 'templates', 'interactions', 'messages.html'));
});

app.get('/notifications', (req, res) => {
    res.sendFile(path.join(__dirname, 'templates', 'interactions', 'notifications.html'));
});

app.get('/profile', (req, res) => {
    res.sendFile(path.join(__dirname, 'templates', 'profile', 'index.html'));
});

// Handle 404
app.use((req, res) => {
    res.status(404).send('Page not found');
});

// Start server
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
}); 