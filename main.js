// main.js - Entry point for the application
// Import the Express app
const app = require('./app');

// For Vercel deployment, we need to export the Express app
module.exports = app;