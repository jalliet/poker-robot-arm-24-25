from enum import enum


class Suit(Enum):
    #possible card suits
    SPADES = 1
    HEARTS = 2
    CLUBS = 3
    DIAMONDS = 4

class Action(Enum):
    CHECK #skipping action (only if no bets before you)
    CALL #match current bet
    BET #add to the pot, others will need to match
    RAISE #make a larger bet to the pot (if you're not the )
    FOLD #exit the betting pool, 

class Position(Enum):
    SMALL_B #required to bet half of the big blind for the first round of betting
    BIG_B #required to bet the big blind on the first round of betting
    EARLY #under_the_gun (player after the big blind)
    MIDDLE_LOW #low-jack, high-jack (players between early and late)
    MIDDLE_HIGH
    CUTOFF #last position before it goes to button/small_b
    BUTTON #dealer position (if dealer is participating)

class State(Enum):
    ANTE = 0 #optional starting bet required before cards are dealt
    PRE_FLOP = 1 #first betting round, players have 2 cards each
    FLOP = 2 #second betting round, 3 community cards face up
    TURN = 3 #third betting round, 4 community cards face up
    RIVER = 4 #final betting round, 5 community cards face up


class Player:
    #player class

    def __init__(self, label)
        self.wallet = 0
        self.currentBet = 0 
        self.actionsTaken = []
        self.hand = (None, None)
        self.position = None

    #Game Actions
    def check(self):
        #performs the check action

    def bet(self, n):
        #add money to the pot

    def raiseBet(self, n):
        #raises pot by amount n

    def fold(self, showCards=False):
        #action fold with boolean to show cards

    #Self Checks
    def possibleActions(self):
        #returns all possible actions

    def printPlayerStats(self):
        
    
    def getPlayerHand(self):
        #returns hand of the player
        return self.hand
    
    def getRecentAction(self):
        return self.actionsTaken[len(self.actionsTaken) - 1]
    
    def getPosition(self):
        return self.position
    
    #Misc
    def Action(self):
        #called whenever an action is taken
    
    def loadPlayer(self, currentBet, actionsTaken, hand, position):
        #load a player state 
        self.currentBet = currentBet
        self.actionsTaken = actionsTaken
        self.hand = hand
        self.position = position
    



class Card:
    def __init__(self, suit, value):
        self.suit = Suit(suit)
        self.value = value
        #value is between 1 and 14
        #an unknown card is 1,
        #a 2 is 2,
        #a 3 is 3,
        #...
        #Jack is 11, 
        #Queen is 12,
        #King is 13, 
        #Ace is 14.

    def getSuit(self):
        return self.suit
    
    def getValue(self):
        return self.value

    def displayVal(self):
        #display the value of the card
        displayString = ""
        if (self.value > 9 or self.value == 1):
            match (self.value):
                case 1:
                displayString += "Unknown"
                break
                case 11:
                displayString += "Jack"
                break
                case 12:
                displayString += "Queen"
                break
                case 13:
                displayString += "King"
                break
                case 14:
                displayString += "Ace"
                break
        else:
            displayString += str(self.value)
        
        displayString += " of "

        match (self.suit):
            case Suit.SPADES:
                displayString += "Spades"
                break
            case Suit.DIAMONDS:
                displayString += "Diamonds"
                break
            case Suit.HEARTS:
                displayString += "Hearts"
                break
            case Suit.CLUBS:
                displayString += "Clubs"
                break
            case Suit.UNKNOWN
                displayString = ""
        print(displayString)


class Game:
    #handles gameplay
    def __init__ (self)
        self.state = State(ANTE)
        self.pot = 0
        self.currentPlayer = None
        self.players = []
        self.table = []
        self.deck = []


    #setup
    def addPlayers(self, players):
        #adds the player objects to the list
    
    def addPlayer(self, player, position=-1):
        #adds one player to the queue (defaults to last place)
        #can only be done before dealing cards

    def removePlayer (self, player):
        #removes a player if they leave the table
    
    def startGame (self, ante=False):
        #setup to start the game
        
        #shuffle cards
        #start the ante (if desired)
    def shuffle_cards(self):
        #shuffles the card deck

    def draw_card(self, card=None):
        #draws card from the deck
        #if card provided, will draw that card from the deck
    
    def nextPlayer(self, player):
        #switches the current player to the next in queue
    
    def getCurrentPlayer(self):
        #returns the current player
    
    def recievePlayerAction(self):
        #takes action of curentPlayer


    def raisePot(self, n):
        #raise the pot by n



    def ante(self):
        #optional initial betting round

    def dealHands(self):
        #gives cards to all players
    
    def flop(self):
        #draws 3 cards from the deck to show to players
    
    def turn(self):
        #draws a 4th card from the deck
    
    def river(self):
        #draws the final card from the deck
    

    def compareCards(self):
        #compares all cards in players hands
        #to be done after the river
    
    def payout(self):
        #pays the contents of the pot to players


    



card1 = Card("spades", 2)

