from enum import enum


class Suit(Enum):
    SPADES = 0
    HEARTS = 1
    CLUBS = 2
    DIAMONDS = 3

class Player:
    def __init__(self)
        self.currentBet = 0
        self.raised = 0
        self.actionsTaken = []
        self.hand = (None, None)

    def check(self):
        
    def raiseBet(self, n):

    def fold(self):

    def possibleActions(self):




class Card:
    def __init__(self, suit, value):
        self.suit = suit
        self.value = value

    def displayVal(self):
        displayString = ""
        match (self.suit):
            case Suit.SPADES:
                break
            case Suit.DIAMONDS:
                break
            case Suit.HEARTS:
                break
            case Suit.CLUBS:

                break
            default:
                print("something went wrong")


class Game:
    def __init__ (self, players)
        self.pot = 0
        self.players = players if len(players) != 0 else []
        self.table = []
        self.deck = []


        
    def 




card1 = Card("spades", 2)

