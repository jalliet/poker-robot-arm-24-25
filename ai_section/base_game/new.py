from typing import List, Set, Dict, Tuple, Type

class Game:                          # Game object
    def __init__(self) -> None:
        self.deck = full_deck
        self.community_cards: List[Type[Card]] = []
        self.players: List[Type[Player]] = []
        self.actions: List[Type[Action]] = []            # History of actions throughout the game
        self.call_amount: int = -1        # Minimum amount to call
        self.game_pot = 0
        self.cur_player = 0
        self.progress_counter = 0
        
    def deal():                      # Cards from deck are assigned, 2 to each player and the 5 community cards are dealt (face down)
        pass

    def flop():                      # First three community cards are flipped over
        pass

    def turn(): 
        pass

    def river():
        pass
    
    def get_pot():
        pass
    
    def evaluate_hands():
        pass
    
    def set_player(self, num):
        i = 0
        for x in range(num):
            self.add_player(x)
    
    def add_player(self, id):
        self.players.append(Player(id))
        
    def check(self, player):
        highest_stake = 0
        for people in self.players:
            if people.stake > highest_stake:
                highest_stake = people.stake
        
        if player.stake < highest_stake:
            return -1
        return 0

    def bet(self, player, n):
        if self.wallet < n:
            return -1
        player.stake += n
        player.wallet -= n
        self.game_pot += n
        return 0

    def raiseBet(self, player, n):
        if self.wallet < n:
            return -1
        player.stake += n
        player.wallet -= n
        self.game_pot += n
        return 0

    def fold(self, player, showCards=False):
        self.players.remove(player)
        
    def startGame (self):
        #setup to start the game
        
        #shuffle cards
        #start the ante (if desired)
        pass
    
    def shuffle_cards(self):
        #shuffles the card deck
        pass

    def draw_card(self, card=None):
        #draws card from the deck
        #if card provided, will draw that card from the deck
        pass
    
    def nextPlayer(self, player):
        #switches the current player to the next in queue
        pass
    
    def getCurrentPlayer(self):
        #returns the current player
        pass
    
    def recievePlayerAction(self):
        #takes action of curentPlayer
        pass
        


class Player:
    def __init__(self, id, init_cash) -> None: # Added ID for players
        self.id = id
        self.wallet = init_cash
        self.stake: bool = None
        self.hand: Tuple[Type[Card]] = ()
    
class Action:
    def __init__(self) -> None:
        pass
        
class Card:
    def __init__(self, num: int, suit: str) -> None:
        self.num = num  # 1-10 is A-10, J: 11, Q:12, K:13
        self.suit = suit # Character representing the suit
        self.public: bool = False

    def __repr__(self) -> str:
        string = str(self.num) + self.suit

        if len(string) < 3:      # Ensures the output is always 3 characters long
            return "0" + string
        return string
        

if __name__ == "__main__":
    full_deck = List[Type[Card]]
    players = List[Type[Player]]
    
    num_of_players = 4
    
    for i in range(len(num_of_players)):
        players.append(Player(id))
    
    
    
    