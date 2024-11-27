import requests
# Change server to ip of poker ai server
SERVER = "http://0.0.0.0:666/"

while True:
    print("What move has been conducted?")
    move = input("").lower()
    match move:
        case "fold": 
            requests.post(SERVER, json={"move":"fold"})
        case "check":
            requests.post(SERVER, json={"move":"check"})
        case "raise":
            amount = input("What is the stake?")
            requests.post(SERVER, json={"move":"raise", "amount":amount})