from enum import Enum


class Suit(Enum):
    SPADES = 0
    HEARTS = 1
    CLUBS = 2
    DIAMONDS = 3

class Player:
    def __init__(self):
        self.currentBet = 0
        self.raised = 0
        self.actionsTaken = []
        self.hand = (None, None)

    def check(self):
        pass

    def raiseBet(self, n):
        pass

    def fold(self):
        pass

    def possibleActions(self):
        pass


class Card:
    def __init__(self, suit, value):
        self.suit = suit
        self.value = value

    def displayVal(self):
        displayString = ""
        match (self.suit):
            case Suit.SPADES:
                pass
            case Suit.DIAMONDS:
                pass
            case Suit.HEARTS:
                pass
            case Suit.CLUBS:
                pass



class Game:
    def __init__ (self, players):
        self.pot = 0
        self.players = players if len(players) != 0 else []
        self.table = []
        self.deck = []


    




card1 = Card("spades", 2)
