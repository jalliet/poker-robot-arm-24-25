from http.server import BaseHTTPRequestHandler, HTTPServer
import time

#these don't need to change
hostName = "0.0.0.0"
serverPort = 666

class ArmServer(BaseHTTPRequestHandler):
    # check you're on the right page
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type","text/html")
        self.end_headers()
        self.wfile.write(bytes("<html><head><title>Arm Server Page</title></head>", "utf-8"))
        #self.wfile.write(bytes("<p>Request: %s</p>" %self.path, "utf-8"))
        self.wfile.write(bytes("<body><p>This is the Arm Server.</p> </body>","utf-8"))
        self.wfile.write(bytes("</html>","utf-8"))

    # recieve data
    def do_POST(self):
        print("ARM: Recieved POST")
        content_length = int(self.headers['Content-length'])
        post_data_bytes = self.rfile.read(content_length)
        print("ARM: %s" % post_data_bytes)



if __name__ == "__main__":
    webServer = HTTPServer((hostName, serverPort), ArmServer)
    print("Server started http://%s:%s$ "% (hostName, serverPort))

    try: 
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
    