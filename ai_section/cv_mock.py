from time import sleep
import requests
# Change server to ip of poker ai server
SERVER = "http://localhost:666/"

with open("./ai_section/game2.txt") as file:
    lines = [line.rstrip() for line in file]

for line in lines:
    type, player, action, amount = line.split(",")
    
    match type:
        case "setPlayers": 
            requests.post(SERVER, json={"type":"setPlayers", "player_count":player})
        case "action":
            requests.post(SERVER, json={"type":"action", "action":action, "player":player, "amount":amount})
        case "showdown":
            requests.post(SERVER, json={"type":"showdown", "community":["2h","4h","9d","Kh","2c"], "hands":[["Qh", "7h"], ["Kd", "2s"]]})
            
    sleep(1)
        