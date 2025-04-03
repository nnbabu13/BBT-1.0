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

                # Update highest bankroll if needed
                highest_bankroll = session['highest_bankroll']
                if new_bankroll > highest_bankroll:
                    session['highest_bankroll'] = float(new_bankroll)
                    highest_bankroll = new_bankroll
                
                # Modified Oscar Grind strategy for next bet
                # Check if net profit < highest bankroll + 1 unit
                target_threshold = highest_bankroll + float(session['base_bet'])
                
                if new_bankroll < target_threshold and (session['net_profit'] + round_profit) < session['profit_target']:
                    # Increase bet by 1 unit after a win if we haven't reached threshold
                    next_bet = float(actual_bet) + float(session['base_bet'])
                    logging.debug(f"Win: Increasing bet to {next_bet} (threshold not reached)")
                else:
                    # Reset to base bet if we reached threshold or profit target
                    next_bet = float(session['base_bet'])
                    if new_bankroll >= target_threshold:
                        flash(f'Reached highest bankroll + 1 unit threshold! Bet reset to base amount.', 'success')
                    if (session['net_profit'] + round_profit) >= session['profit_target']:
                        flash('Profit target reached! Bet reset to base amount.', 'success')
            else:
                # Loss scenario
                round_profit = -float(actual_bet)
                new_bankroll = session['current_bankroll'] + round_profit
                
                # Keep bet the same after a loss (Oscar Grind strategy)
                next_bet = float(actual_bet)
                logging.debug(f"Loss: Keeping bet at {next_bet}")
            
            # Ensure bet doesn't exceed bankroll
            if next_bet > new_bankroll:
                next_bet = float(new_bankroll)
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
