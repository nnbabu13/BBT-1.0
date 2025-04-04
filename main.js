// main.js - Entry point for the application
// Import the Express app
const app = require('./app');

// For Vercel deployment, we need to export the Express app
module.exports = app;

// Start the server if this file is executed directly
if (require.main === module) {
  const PORT = process.env.NODE_PORT || 3000;
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Baccarat Oscar Grind Tracker started on http://0.0.0.0:${PORT}`);
  });
}