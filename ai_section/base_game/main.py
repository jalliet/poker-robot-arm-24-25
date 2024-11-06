from typing import List, Set, Dict, Tuple, Type
from treys import Card as TreyCard, Evaluator

class Game:                          # Game object
    def __init__(self) -> None:
        self.deck = full_deck
        self.community_cards: List[Type[Card]] = []
        self.players: List[Type[Player]] = []
        self.actions: List[Type[Action]] = []            # History of actions throughout the game
        self.call_amount: int = -1        # Minimum amount to call
        
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
    
    def evaluate_hands(self, hands):
        _community_cards = []
        for card in self.community_cards:
            _community_cards.append(TreyCard.new(str(card)))
        
        hand_scores = {}
        for hand in hands:
            hand = [TreyCard.new(str(hand[0])), TreyCard.new(str(hand[1]))]
            hand_scores[hand] = Evaluator.evaluate(_community_cards, hand)



class Player:
    def __init__(self) -> None:
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
