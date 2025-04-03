import os
import logging
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from decimal import Decimal, ROUND_DOWN

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key-for-development")

# Routes
@app.route('/', methods=['GET', 'POST'])
def index():
    # Clear any existing session data when returning to home page
    if request.method == 'GET':
        session.clear()
    
    # Default values
    default_bankroll = 1000
    default_base_bet = 10
    default_profit_target = 100
    
    if request.method == 'POST':
        try:
            # Get form values and convert to Decimal for precise calculations
            bankroll = Decimal(request.form.get('bankroll', default_bankroll))
            base_bet = Decimal(request.form.get('base_bet', default_base_bet))
            profit_target = Decimal(request.form.get('profit_target', default_profit_target))
            
            # Validate inputs
            if bankroll <= 0 or base_bet <= 0 or profit_target <= 0:
                flash('All values must be positive numbers.', 'danger')
                return render_template('index.html', 
                                      bankroll=default_bankroll, 
                                      base_bet=default_base_bet, 
                                      profit_target=default_profit_target)
                
            if base_bet > bankroll:
                flash('Base bet cannot be larger than bankroll.', 'danger')
                return render_template('index.html', 
                                      bankroll=default_bankroll, 
                                      base_bet=default_base_bet, 
                                      profit_target=default_profit_target)
            
            # Initialize session variables
            session['starting_bankroll'] = float(bankroll)
            session['current_bankroll'] = float(bankroll)
            session['highest_bankroll'] = float(bankroll)
            session['base_bet'] = float(base_bet)
            session['profit_target'] = float(profit_target)
            session['current_bet'] = float(base_bet)
            session['net_profit'] = 0
            session['bet_history'] = []
            session['round_number'] = 1
            session['session_active'] = True
            
            # Redirect to session page
            return redirect(url_for('bet_session'))
            
        except (ValueError, TypeError):
            flash('Please enter valid numbers for all fields.', 'danger')
    
    # Render index template with default values
    return render_template('index.html', 
                          bankroll=default_bankroll, 
                          base_bet=default_base_bet, 
                          profit_target=default_profit_target)

@app.route('/session', methods=['GET', 'POST'])
def bet_session():
    # Check if session is initialized
    if 'session_active' not in session or not session['session_active']:
        flash('Please start a new session first.', 'warning')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            # Get bet result
            result = request.form.get('result')
            actual_bet = Decimal(request.form.get('actual_bet', 0))
            suggested_bet = Decimal(session['current_bet'])
            
            # Validate bet amount
            if actual_bet <= 0:
                flash('Bet amount must be positive.', 'danger')
                return redirect(url_for('bet_session'))
            
            if actual_bet > session['current_bankroll']:
                flash('Bet amount cannot exceed current bankroll.', 'danger')
                return redirect(url_for('bet_session'))
            
            # Record if bet matches suggestion
            bet_matches_suggestion = (actual_bet == suggested_bet)
            
            # Update bankroll and history based on result
            round_profit = 0
            next_bet = float(session['base_bet'])  # Default to base bet
            
            if result == 'win':
                # Win scenario
                round_profit = float(actual_bet)
                new_bankroll = session['current_bankroll'] + round_profit
                base_bet = float(session['base_bet'])
                
                # Get current highest bankroll
                highest_bankroll = session['highest_bankroll']
                target_threshold = highest_bankroll + base_bet
                
                # Case 2: If Win takes bankroll > highest_bankroll + 1 base unit
                if new_bankroll > target_threshold:
                    # Update highest bankroll
                    session['highest_bankroll'] = float(new_bankroll)
                    logging.debug(f"Win exceeded threshold, updating highest bankroll to {new_bankroll}")
                    
                    # Reset to base bet (ignore standard progression)
                    next_bet = base_bet
                    flash(f'Bankroll exceeded highest + 1 unit threshold! Bet reset to base amount.', 'success')
                    logging.debug(f"Win: Resetting bet to {next_bet} (exceeded threshold)")
                    
                # Case 1: Win takes bankroll ≤ highest_bankroll + 1 base unit
                else:
                    # Check if we've exactly reached the threshold
                    if new_bankroll == target_threshold:
                        # Reset to base bet
                        next_bet = base_bet
                        flash(f'Reached highest bankroll + 1 unit threshold! Bet reset to base amount.', 'success')
                        logging.debug(f"Win: Resetting bet to {next_bet} (reached threshold exactly)")
                    
                    # If profit target reached
                    elif (session['net_profit'] + round_profit) >= session['profit_target']:
                        # Reset to base bet
                        next_bet = base_bet
                        flash('Profit target reached! Bet reset to base amount.', 'success')
                        logging.debug(f"Win: Resetting bet to {next_bet} (profit target reached)")
                    
                    # Normal progression - increase bet by 1 unit
                    else:
                        # First, calculate standard next bet (increase by 1 unit)
                        standard_next_bet = float(actual_bet) + base_bet
                        
                        # Calculate where we'd end up if we bet standard_next_bet and win
                        potential_bankroll = new_bankroll + standard_next_bet
                        
                        # Check if that would exceed threshold
                        if potential_bankroll > target_threshold:
                            # Calculate exact bet needed to reach threshold on next win
                            exact_bet = target_threshold - new_bankroll
                            
                            # Convert to nearest multiple of base bet (floor)
                            bet_units = max(1, int(exact_bet / base_bet))
                            next_bet = bet_units * base_bet
                            
                            logging.debug(f"Win: Adjusting next bet to {next_bet} to prevent exceeding threshold on next win")
                        else:
                            # Standard progression - increase by 1 unit
                            next_bet = standard_next_bet
                            logging.debug(f"Win: Increasing bet to {next_bet} (standard progression)")
                
                # Ensure bet amount is in multiples of base bet
                next_bet = round(next_bet / base_bet) * base_bet
                if next_bet < base_bet:
                    next_bet = base_bet
            else:
                # Loss scenario
                round_profit = -float(actual_bet)
                new_bankroll = session['current_bankroll'] + round_profit
                base_bet = float(session['base_bet'])
                
                # Keep bet the same after a loss (Oscar Grind strategy)
                next_bet = float(actual_bet)
                
                # Ensure bet amount is in multiples of base bet
                next_bet = round(next_bet / base_bet) * base_bet
                if next_bet < base_bet:
                    next_bet = base_bet
                
                logging.debug(f"Loss: Keeping bet at {next_bet}")
            
            # Ensure bet doesn't exceed bankroll
            if next_bet > new_bankroll:
                # Find the largest multiple of base_bet that fits within the bankroll
                base_bet = float(session['base_bet'])
                bet_units = int(new_bankroll / base_bet)
                next_bet = bet_units * base_bet
                if next_bet < base_bet:
                    next_bet = min(base_bet, float(new_bankroll))  # Minimum bet is 1 unit or less if bankroll is too low
                logging.debug(f"Limiting bet to {next_bet} (cannot exceed bankroll)")
            
            # Update session data
            round_number = session['round_number']
            session['current_bankroll'] = float(new_bankroll)
            session['net_profit'] = session['net_profit'] + round_profit
            session['current_bet'] = float(next_bet)
            session['round_number'] = round_number + 1
            
            # Add to history with next suggested bet
            bet_history = session.get('bet_history', [])
            bet_history.append({
                'round': round_number,
                'bet_amount': float(actual_bet),
                'result': result,
                'profit_loss': round_profit,
                'bankroll': float(new_bankroll),
                'next_bet': float(next_bet),
                'followed_suggestion': bet_matches_suggestion
            })
            session['bet_history'] = bet_history
            
            # Check for bankruptcy
            if new_bankroll <= 0:
                flash('Bankruptcy! You have lost all your bankroll.', 'danger')
            
            # Check if profit target has been reached
            if session['net_profit'] >= session['profit_target']:
                flash(f'Congratulations! You have reached your profit target of ${session["profit_target"]}.', 'success')
            
            return redirect(url_for('bet_session'))
            
        except (ValueError, TypeError):
            flash('Please enter valid numbers for bet amount.', 'danger')
    
    return render_template('session.html', 
                          starting_bankroll=session['starting_bankroll'],
                          current_bankroll=session['current_bankroll'], 
                          highest_bankroll=session['highest_bankroll'],
                          base_bet=session['base_bet'],
                          profit_target=session['profit_target'],
                          current_bet=session['current_bet'],
                          net_profit=session['net_profit'],
                          bet_history=session.get('bet_history', []),
                          round_number=session['round_number'])

@app.route('/reset', methods=['POST'])
def reset_session():
    session.clear()
    flash('Session has been reset.', 'info')
    return redirect(url_for('index'))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('index.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
