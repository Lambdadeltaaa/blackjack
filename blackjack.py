# Imports
from flask import render_template, session, redirect, url_for
from random import shuffle
from functools import wraps

class Card:
    def __init__(self, suit, value):
        self.suit = suit
        self.value = value

    def __repr__(self):
        return f"{self.value}_of_{self.suit}"


class Deck:
    suits = ['hearts', 'diamonds', 'clubs', 'spades']
    values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'jack', 'queen', 'king', 'ace']

    def __init__(self):
        self.cards = [Card(suit, value) for suit in self.suits for value in self.values]
        shuffle(self.cards)

    def draw(self):
        return self.cards.pop()


def calculate_hand_value(hand):
    total = 0;
    aces = 0;

    value_map = {'2': 2, '2': 2, '3': 3, '4': 4, 
                 '5': 5, '6': 6, '7': 7, '8': 8, 
                 '9': 9, '10': 10, 'jack': 10, 'queen': 10, 
                 'king': 10, 'ace': 11}
    
    for card in hand:
        if card.value == 'ace':
            aces += 1

        total += value_map[card.value]

    while (total > 21 and aces != 0):
        total -= 10
        aces -= 1

    return total


def blackjack(user):
    return user['total_value'] == 21 and len(user['hand']) == 2


def end_game(result, player, dealer, game):
    if result == 'Blackjack':
        session['player_cash'] += round(session['bet_amount'] * 2.5)
        player['cash'] = session['player_cash']

    if result == 'Win':
        session['player_cash'] += session['bet_amount'] * 2
        player['cash'] = session['player_cash']

    if result == 'Tie':
        session['player_cash'] += session['bet_amount'] 
        player['cash'] = session['player_cash']

    session['game_result'] = result
    game['result'] = session['game_result']

    session['game_end'] = True
    game['ended'] = session['game_end']

    session['game_in_progress'] = False

    return render_template("play.html", player=player, dealer=dealer, game=game)


def prevent_actions_when_unavailable(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Checks if player try to access buttons when new game has not been initialised
        if session.get('dealer_hand') is None or session.get('player_hand') is None:
            return redirect(url_for('new_game'))
        
        # Check if the user has bet or not
        if session.get('bet_amount') is None:
            return redirect(url_for('play'))
        
        # Check if the game has ended
        if session.get('game_end') == True:
            return redirect(url_for('play'))
        
        # Check if the player is given the choice of buying insurance and splitting
        if session.get('can_buy_insurance') == True or session.get('can_split') == True:
            return redirect(url_for('play'))
            
        return f(*args, **kwargs)
    
    return decorated_function
