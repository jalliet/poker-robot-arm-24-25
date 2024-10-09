from typing import List, Set, Dict, Tuple, Type

class Game:                          # Game object
    def __init__(self) -> None:
        self.deck = full_deck
        self.community_cards: List[Type[Card]] = []
        self.players: List[Type[Player]] = []
        self.actions: List[Type[Action]] = []            # History of actions throughout the game
        self.call_amount: int = -1        # Minimum amount to call
        
    def deal(self):                      # Cards from deck are assigned, 2 to each player and the 5 community cards are dealt (face down)
        pass

    def flop(self):                      # First three community cards are flipped over
        pass

    def turn(self): 
        pass

    def river(self):
        pass
    
    def get_pot(self):
        pass
    
    def evaluate_hands(self):
        pass


class Player:
    def __init__(self) -> None:
        self.stake: int = 0
        self.balance: int = 0
        self.is_active: bool = False
        self.all_in: bool = False
        self.hand: Tuple[Type[Card]] = ()

    def can_check(self):
        pass

    def call(self):
        pass

    def raise_bet(self):
        pass

    def fold(self):
        pass

    def check(self):
        pass

    
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
        


full_deck = List[Type[Card]]
