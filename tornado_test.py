# Testing with a simple tornado server

# Imports
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web

# Websocket Handling
class WSHandler(tornado.websocket.WebSocketHandler):
	
	testVal = 3
	
	def open(self):
		print("New Tornado Connection Opened")
		self.write_message("Connected to tornado test server")
	
	def on_close(self):
		print("Tornado Connection Closed")
		
	def on_message(self, message):
		if(message == "get"):
			self.write_message(str(self.testVal))
		else:
			print("Received:" + message)
		
		
	def check_origin(self, origin):
		return True
		
application = tornado.web.Application([
	(r'/ts', WSHandler),
])

def main():
	
	http_server = tornado.httpserver.HTTPServer(application)
	http_server.listen(8888)
	tornado.ioloop.IOLoop.current().start()
	
if __name__ == "__main__":
    main()
