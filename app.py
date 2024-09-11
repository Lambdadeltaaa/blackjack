# Imports 
from flask import Flask, render_template, request, session, redirect
from flask_session import Session

from blackjack import Card, Deck, calculate_hand_value, end_game, blackjack, prevent_actions_when_unavailable

# Flask Configurations
app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Home Page
@app.route("/")
def index():
    session['player_cash'] = 10000
    return render_template("index.html")


# The Game
@app.route("/new_game")
def new_game():
    # Dont allow the user to new game when game is ongoing
    if session.get('game_in_progress') == True:
        return redirect('/play')

    # Initializing the game
    session['bet_amount'] = None

    session['deck'] = Deck()
    session['dealer_hand'] = []
    session['player_hand'] = []
    
    session['game_end'] = False
    session['game_in_progress'] = True
    session['game_result'] = None

    session['can_double_down'] = True

    session['can_buy_insurance'] = False
    session['bought_insurance'] = None
    
    session['can_split'] = False
    session['splitted'] = None
    
    # Draw two cards for both the player and the dealer
    for _ in range(2):
        session['dealer_hand'].append(session['deck'].draw())
        session['player_hand'].append(session['deck'].draw())

    return redirect("/play")


@app.route("/play")
def play():
    # Prevent the user from start game when new game has not been initialised
    if session.get('dealer_hand') is None or session.get('player_hand') is None:
        return redirect("/new_game")
    

    # Calculate stuffs
    player = {'hand': session['player_hand'],
              'total_value': calculate_hand_value(session['player_hand']),
              'cash': session['player_cash'],
              'bet_amount': session['bet_amount']
             }
    
    dealer = {'hand': session['dealer_hand'],
              'first_card_value': calculate_hand_value([session['dealer_hand'][0]]),
              'total_value': calculate_hand_value(session['dealer_hand']),
             }
    
    game = {'ended': session['game_end'],
            'result': session['game_result'],
            'can_double_down': session['can_double_down'],
            'can_buy_insurance': session['can_buy_insurance'],
            'bought_insurance': session['bought_insurance']
            }
    

    # Stop everything after game has ended
    if game['ended'] == True and game['result'] is not None:
        return render_template("play.html", player=player, dealer=dealer, game=game)


    # Betting mechanic
    if player['bet_amount'] is None:
        return render_template("bet.html", player=player)
    

    # Game Logic:   
    # Logic for checking who got blackjack instantly and insurance buying mechanic
    if blackjack(dealer) and blackjack(player):
        return end_game('Tie', player, dealer, game)
    
    if blackjack(player):
        return end_game('Blackjack', player, dealer, game)
    
    if dealer['first_card_value'] == 11 and game['bought_insurance'] is None:    
        session['can_buy_insurance'] = True
        game['can_buy_insurance'] = session['can_buy_insurance']
        return render_template("play.html", player=player, dealer=dealer, game=game)
    
    if game['bought_insurance'] == True and blackjack(dealer):
        session['player_cash'] += player['bet_amount']
        player['cash'] = session['player_cash']
        return end_game('Loss', player, dealer, game)

    if blackjack(dealer):
        return end_game('Loss', player, dealer, game)
    

    # ADD SPLITTING HERE


    # Logic for checking who busted
    if (player['total_value'] > 21):
        return end_game('Loss', player, dealer, game)

    if (dealer['total_value'] > 21 and player['total_value'] <= 21):
        return end_game('Win', player, dealer, game)

    
    # Logic for checking who wins at the end
    if game['ended'] == True:
        if player['total_value'] > dealer['total_value']:
            return end_game('Win', player, dealer, game)

        elif player['total_value'] == dealer['total_value']:
            return end_game('Tie', player, dealer, game)
            
        else:
            return end_game('Loss', player, dealer, game)


    # Returns the existing version, game has not ended yet
    return render_template("play.html", player=player, dealer=dealer, game=game)


@app.route("/hit")
@prevent_actions_when_unavailable
def hit():    
    session['player_hand'].append(session['deck'].draw())
    session['can_double_down'] = False
    return redirect("/play")


@app.route("/double_down")
@prevent_actions_when_unavailable
def double_down():
    if session['can_double_down'] == False:
        return redirect("/play")
    
    if session['bet_amount'] > session['player_cash']:
        return redirect("/play")
    
    session['player_cash'] -= session['bet_amount']
    session['bet_amount'] *= 2

    session['player_hand'].append(session['deck'].draw())
    session['can_double_down'] = False

    return redirect("/stand")


@app.route("/stand")
@prevent_actions_when_unavailable
def stand():  
    # Dealer keeps hitting until it reaches at least 17
    while True:
        dealer_total = calculate_hand_value(session['dealer_hand'])

        if dealer_total >= 17:
            break

        session['dealer_hand'].append(session['deck'].draw())
    
    session['game_end'] = True
    return redirect("/play")


@app.route("/bet", methods=["GET", "POST"])
def bet():
    # prevent the user from accessing this when the game has not even started yet
    if session.get('dealer_hand') is None or session.get('player_hand') is None:
            return redirect("/new_game")
    
    # pretty much only lets them input if theres still no bet
    if request.method == "POST" and session['bet_amount'] is None:
        bet = request.form.get('bet_amount')

        if (not bet) or ("." in bet):
            return redirect("/play")
        
        try:         
            bet = int(bet)
        except ValueError:
            return redirect("/play")
        
        if bet > 0 and bet <= session['player_cash']:
            session['bet_amount'] = bet
            session['player_cash'] -= bet
        
    return redirect("/play")


@app.route("/insurance", methods=["GET", "POST"])
def insurance():
    # prevent the user from accessing this when the game has not even started yet
    if session.get('dealer_hand') is None or session.get('player_hand') is None:
        return redirect("/new_game")
    
    # pretty much only lets them input if insurance is available
    if request.method == "POST" and session['can_buy_insurance']:
        choice = request.form.get("insurance")
        
        if choice in ['Yes', 'No']:
            if (choice == 'Yes') and (round(session['bet_amount'] / 2) <= session['player_cash']):
                session['player_cash'] -= round(session['bet_amount'] / 2)
                session['bought_insurance'] = True
                session['can_buy_insurance'] = False
                
            else:
                session['bought_insurance'] = False
                session['can_buy_insurance'] = False
               
    return redirect("/play")
    

# User Account Configurations
@app.route("/stats")
def stats():
    return "statistics"


@app.route("/settings")
def settings():
    return "settings"


@app.route("/login")
def login():
    return "login"


@app.route("/logout")
def logout():
    return "logout"


@app.route("/register")
def register():
    return "register"


# Debugging
if __name__ == "__main__":
    app.run(debug=True)