from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import json
import main as main

hostName = "10.205.105.36"
serverPort = 666

# Define a custom HTTPServer to pass attributes
class ArmHTTPServer(HTTPServer):
    def __init__(self, server_address, handler_class, game):
        super().__init__(server_address, handler_class)
        self.game = game

class ArmServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("<html><head><title>Arm Server Page</title></head>", "utf-8"))
        self.wfile.write(bytes("<body><p>This is the Arm Server.</p></body>", "utf-8"))
        self.wfile.write(bytes("</html>", "utf-8"))

    def do_POST(self):
        print("ARM: Received POST")
        content_length = int(self.headers['Content-length'])
        post_data_bytes = self.rfile.read(content_length)
        post_data = json.loads(post_data_bytes.decode('utf-8'))
        print(str(post_data))

        # Access the game object from the server instance
        game = self.server.game
        
        match post_data["type"]:
            case "action":
                game.process_turn(post_data["action"], int(post_data["player"]), int(post_data["amount"]))
            case "setPlayers":
                game.set_player(post_data["player_count"])
            case "showdown":
                game.evaluate_hands(post_data["community"], post_data["hands"])
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

if __name__ == "__main__":
    # Initialize the Game instance
    my_game = main.Game()
    
    # Function to start the server
    def start_server():
        webServer = ArmHTTPServer((hostName, serverPort), ArmServer, my_game)
        print("Server started at http://%s:%s" % (hostName, serverPort))
        try:
            webServer.serve_forever()
        except KeyboardInterrupt:
            pass
        webServer.server_close()
        print("Server stopped.")
    
    # Run server in a separate thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Keep the main thread running (useful if integrating with UI or other main-loop logic)
    my_game.run_gui()
    
    print("Main thread exiting.")