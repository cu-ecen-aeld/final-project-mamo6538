# This should run upon startup and operate in the background of hbs_master ?? might be useful to have that database.

# Imports
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web

import json

# Websocket Handling
class WSHandler(tornado.websocket.WebSocketHandler):
	
	testVal = 3
	
	#enable cross domain origin (idk)
	def check_origin(self, origin):
		return True
	
	def open(self):
		print("New Tornado Connection Opened")
		self.write_message("Connected to tornado test server")
	
	def on_close(self):
		print("Tornado Connection Closed")
		
	def on_message(self, message):
		if(message == "get"):
			sensor_data = {"timestamp" : '1992',
			"water_lvl" : 50,
			"food_bowl_lvl" : 33,
			"food_res_lvl" : 45,
			"treat_lvl" : 90,
			"pet_dist" : 8,
			"temp": 75}
			json_str = json.dumps(sensor_data, default=str)
			# send back
			self.write_message(json_str)
		elif ('action' in message):
			print("action")
			d = json.loads(message)
			print(d['action'])
		elif ('settings' in message):
			print("setting")
			print(message['auto_feed'])
		else:
			print("Message received is unknown type")
		
		
	def check_origin(self, origin):
		return True

def make_app():		
	return tornado.web.Application([
		(r'/ts', WSHandler),
	])

def main():
	application = make_app()
	http_server = tornado.httpserver.HTTPServer(application)
	http_server.listen(8888)
	tornado.ioloop.IOLoop.current().start()

	
if __name__ == "__main__":
	main()
