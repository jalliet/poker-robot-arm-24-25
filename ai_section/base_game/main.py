from typing import Set, Dict, Tuple, Type
from treys import Card, Evaluator, Deck

# Copyright (c) 2013 Will Drevo
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

'''
Initialization:
1. Set players from CV, retrieve their ID
2. Append players to list
3. Set cards list
4. Deal cards
5. Initial bet by all players (assuming they have money ready), add to pot
6. Asks player for actions, retrieve action

Possible actions example:
Raise, call, call - end
Check, check, raise - call, call, skip - end
Check, check, check - end
Raise, raise, call - call, skip, skip - end
Check, raise, raise - call, call, skip - end

When ended, advance to next round
'''

class Game:                          # Game object
    def __init__(self) -> None:
        self.deck = Deck()
        self.community_cards: list[Type[Card]] = []
        self.players: list[Type[Player]] = []
        self.actions: list[Type[Action]] = []            # History of actions throughout the game
        self.call_amount: int = -1        # Minimum amount to call
        self.game_pot = 0
        self.cur_player = 0
        self.progress_count = 0
        self.fold_count = 0
        self.round = 0
        
    
    def get_pot(self):
        pass
    
    def evaluate_hands(self, community, hands): 
        print(community)
        print(hands)
        evaluator = Evaluator()  # Create an instance of Evaluator
        hand_scores = {}

        # Convert JSON string arrays to Treys integer-based card representations
        community_cards = [Card.new(card) for card in community]

        for hand in hands:
            hole_cards = [Card.new(card) for card in hand]  # Convert hand strings to integers
            hand_rank = evaluator.evaluate(community_cards, hole_cards)  # Evaluate hand
            hand_scores[tuple(hand)] = hand_rank  # Store result using the original hand as a tuple

        print(hand_scores)
        return hand_scores
            
    
    def end_round(self):
        self.round += 1
        if self.round == 1:
            # send flop to kinematics
            pass
        elif self.round == 2:
            # send turn to kinematics
            pass
        elif self.round == 3:
            # send river to kinematics
            pass
        elif self.round == 4:
            # do showdown
            pass
        self.progress_count = 0
        
    
    def check_end_of_round(self):
        if self.progress_count == len(self.players) - 1:
            self.end_round()
        
    def process_turn(self, action: str, player, n=0):
        print(self.players)
        player = self.players[int(player)]
        
        match action: 
            case "call":
                self.progress_count += 1
            case "check":
                self.progress_count += 1
            case "raise":
                self.raiseBet(player, n)
                self.progress_count = 0

        
    
    def set_player(self, num):      # Input number of players from cv team (including player id)
        for id in range(int(num)):
            self.add_player(id)
    
    def add_player(self, id):
        self.players.append(Player(id))
        
    def check(self, player):    # Checks if player needs to stake
        highest_stake = 0
        for people in self.players:
            if people.stake > highest_stake:
                highest_stake = people.stake
        
        if player.stake < highest_stake:
            return -1
        return 0
    
    def bet(self, player, n):       # Betting (input player and bet amount)
        if player.wallet < n:
            return -1
        player.stake += n
        player.wallet -= n
        self.game_pot += n
        return 0

    def raiseBet(self, player, n):      # Raise (input player and bet amount)
        if player.wallet < n:
            return -1
        player.stake += n
        player.wallet -= n
        self.game_pot += n
        return 0
    
    def call(self, player, highest_stake):      # Call
        change = highest_stake - player.stake
        if self.wallet < change:
            return -1
        self.game_pot += highest_stake - player.stake
        player.stake = highest_stake
        return 0
        
    def fold(self, player, showCards=False):        # Fold, remove players (may add an option to show cards)
        self.players.remove(player)
        
        


class Player:
    def __init__(self, id, init_cash=100) -> None: # Added ID for players
        self.id = id
        self.wallet = init_cash
        self.stake: bool = None
        self.hand: list[Type[Card]] = []

    def __repr__(self) -> str:
        return "Player: ID = " + str(self.id)
    
class Action:
    def __init__(self) -> None:
        pass
        

if __name__ == "__main__":
    full_deck: list[Type[Card]] = []

    players: list[Type[Player]] = []
    
    num_of_players = 4
    
    for i in range(num_of_players):
        players.append(Player(i, 0))
    
    
    
    