// Import required packages
const express = require('express');
const path = require('path');
const session = require('express-session');
const bodyParser = require('body-parser');
const cookieParser = require('cookie-parser');
const logger = require('morgan');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config();

// Initialize Express app
const app = express();

// Configure view engine
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Middleware
app.use(logger('dev'));
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(express.static(path.join(__dirname, 'public')));

// Session configuration
app.use(session({
  secret: process.env.SESSION_SECRET || 'oscar-grind-baccarat-tracker-secret',
  resave: false,
  saveUninitialized: true,
  cookie: { maxAge: 24 * 60 * 60 * 1000 } // 24 hours
}));

// Flash message middleware
app.use((req, res, next) => {
  res.locals.flash = req.session.flash || {};
  delete req.session.flash;
  next();
});

// Oscar Grind strategy calculation functions
function calculateNextBet(currentBankroll, highestBankroll, baseBet, lastBet, lastResult) {
  // Base case: always start with base bet
  if (!lastBet || !lastResult) {
    return baseBet;
  }
  
  const threshold = highestBankroll + parseFloat(baseBet);
  
  if (lastResult === 'win') {
    // If we've already reached the highest bankroll + 1 unit threshold, reset to base bet
    if (currentBankroll >= threshold) {
      return baseBet;
    }
    
    // Calculate standard progression (increase by 1 unit after a win)
    const standardNextBet = parseFloat(lastBet) + parseFloat(baseBet);
    
    // Calculate potential bankroll if we win with standard next bet
    const potentialBankroll = currentBankroll + standardNextBet;
    
    // If potential win would exceed threshold, adjust bet to hit threshold exactly
    if (potentialBankroll > threshold) {
      // Calculate the exact bet needed to reach the threshold
      const adjustedBet = threshold - currentBankroll;
      
      // Ensure the bet is a multiple of base bet (round down)
      const multiplier = Math.floor(adjustedBet / baseBet);
      return Math.max(baseBet, multiplier * baseBet);
    }
    
    return standardNextBet;
  } else {
    // After a loss, maintain the same bet amount
    return parseFloat(lastBet);
  }
}

// Routes
// Index page - Setup form
app.get('/', (req, res) => {
  // Check if session already exists
  if (req.session.betting_session) {
    return res.redirect('/session');
  }
  
  res.render('index');
});

// Process setup form
app.post('/', (req, res) => {
  const starting_bankroll = parseFloat(req.body.starting_bankroll);
  const base_bet = parseFloat(req.body.base_bet);
  const profit_target = parseFloat(req.body.profit_target);
  
  // Validate inputs
  if (isNaN(starting_bankroll) || starting_bankroll <= 0) {
    req.session.flash = { danger: 'Please enter a valid starting bankroll.' };
    return res.redirect('/');
  }
  
  if (isNaN(base_bet) || base_bet <= 0) {
    req.session.flash = { danger: 'Please enter a valid base bet amount.' };
    return res.redirect('/');
  }
  
  if (isNaN(profit_target) || profit_target <= 0) {
    req.session.flash = { danger: 'Please enter a valid profit target.' };
    return res.redirect('/');
  }
  
  // Initialize betting session
  req.session.betting_session = {
    starting_bankroll,
    current_bankroll: starting_bankroll,
    highest_bankroll: starting_bankroll,
    base_bet,
    profit_target,
    current_bet: base_bet,
    round_number: 1,
    bet_history: []
  };
  
  req.session.flash = { success: 'Session started successfully! Good luck!' };
  res.redirect('/session');
});

// Session page - Betting interface
app.get('/session', (req, res) => {
  // Check if session exists
  if (!req.session.betting_session) {
    req.session.flash = { warning: 'No active session found. Please set up a new session.' };
    return res.redirect('/');
  }
  
  const session = req.session.betting_session;
  
  // Check if profit target reached
  if (session.current_bankroll - session.starting_bankroll >= session.profit_target) {
    req.session.flash = { success: `Congratulations! You've reached your profit target of $${session.profit_target.toFixed(2)}!` };
  }
  
  // Check if bankrupt
  if (session.current_bankroll < session.base_bet) {
    req.session.flash = { danger: 'Warning: Your bankroll is now below your base bet amount. Consider resetting or adjusting your strategy.' };
  }
  
  // Calculate net profit
  const net_profit = session.current_bankroll - session.starting_bankroll;
  
  res.render('session', {
    ...session,
    net_profit
  });
});

// Process bet form
app.post('/session', (req, res) => {
  // Check if session exists
  if (!req.session.betting_session) {
    req.session.flash = { warning: 'No active session found. Please set up a new session.' };
    return res.redirect('/');
  }
  
  const session = req.session.betting_session;
  const bet_amount = parseFloat(req.body.bet_amount);
  const result = req.body.result;
  
  // Validate inputs
  if (isNaN(bet_amount) || bet_amount <= 0) {
    req.session.flash = { danger: 'Please enter a valid bet amount.' };
    return res.redirect('/session');
  }
  
  if (!['win', 'loss'].includes(result)) {
    req.session.flash = { danger: 'Invalid result selected.' };
    return res.redirect('/session');
  }
  
  // Check if bet is valid
  if (bet_amount > session.current_bankroll) {
    req.session.flash = { danger: 'Your bet amount exceeds your current bankroll.' };
    return res.redirect('/session');
  }
  
  // Check if bet is a multiple of base bet (with small rounding tolerance)
  const isDivisible = Math.abs(Math.round(bet_amount / session.base_bet) - (bet_amount / session.base_bet)) < 0.0001;
  if (!isDivisible) {
    req.session.flash = { danger: `Your bet amount must be a multiple of your base bet ($${session.base_bet.toFixed(2)}).` };
    return res.redirect('/session');
  }
  
  // Process bet result
  let profit_loss = 0;
  if (result === 'win') {
    profit_loss = bet_amount;
    session.current_bankroll += bet_amount;
  } else {
    profit_loss = -bet_amount;
    session.current_bankroll -= bet_amount;
  }
  
  // Update highest bankroll if needed
  if (session.current_bankroll > session.highest_bankroll) {
    session.highest_bankroll = session.current_bankroll;
  }
  
  // Calculate next bet based on Oscar Grind strategy
  const nextBet = calculateNextBet(
    session.current_bankroll,
    session.highest_bankroll,
    session.base_bet,
    bet_amount,
    result
  );
  
  // Record bet in history
  session.bet_history.unshift({
    round: session.round_number,
    bet_amount,
    result,
    profit_loss,
    bankroll: session.current_bankroll,
    next_bet: nextBet,
    followed_suggestion: bet_amount === session.current_bet
  });
  
  // Update session
  session.round_number += 1;
  session.current_bet = nextBet;
  
  // Save session
  req.session.betting_session = session;
  
  // Add appropriate flash message
  if (result === 'win') {
    req.session.flash = { success: `Congratulations! You won $${bet_amount.toFixed(2)}. Your bankroll is now $${session.current_bankroll.toFixed(2)}.` };
  } else {
    req.session.flash = { info: `You lost $${bet_amount.toFixed(2)}. Your bankroll is now $${session.current_bankroll.toFixed(2)}.` };
  }
  
  res.redirect('/session');
});

// Reset session
app.post('/reset', (req, res) => {
  // Clear betting session
  delete req.session.betting_session;
  
  req.session.flash = { info: 'Your session has been reset. You can start a new session now.' };
  res.redirect('/');
});

// Error handling
// 404 handler
app.use((req, res, next) => {
  res.status(404).render('index', { 
    error: 'Page not found' 
  });
});

// 500 handler
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).render('index', { 
    error: 'Something went wrong! Please try again later.' 
  });
});

// Start server
const PORT = process.env.PORT || 5000;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on port ${PORT}`);
});

module.exports = app;