from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import new
import json

hostName = "localhost"
serverPort = 666

class ArmServer(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)
        self.game = new.Game()
        
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type","text/html")
        self.end_headers()
        self.wfile.write(bytes("<html><head><title>Arm Server Page</title></head>", "utf-8"))
        #self.wfile.write(bytes("<p>Request: %s</p>" %self.path, "utf-8"))
        self.wfile.write(bytes("<body><p>This is the Arm Server.</p> </body>","utf-8"))
        self.wfile.write(bytes("</html>","utf-8"))
        
    def do_POST(self):
        print("ARM: Recieved POST")
        content_length = int(self.headers['Content-length'])
        post_data_bytes = self.rfile.read(content_length)
        print("ARM: %d" % post_data_bytes)
        post_data = json.loads(post_data_bytes.decode('utf-8'))
        
        match post_data["type"]:
            case "action":
                self.game.process_turn(post_data["action"], post_data["player"], post_data["amount"])
            case "setPlayer":
                self.game.set_player(post_data["player_count"])
        
        
if __name__ == "__main__":
    webServer = HTTPServer((hostName, serverPort), ArmServer)
    print("Server started http://%s:%s$ "% (hostName, serverPort))

    try: 
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
        