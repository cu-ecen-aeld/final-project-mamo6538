# pylint: disable=import-not-at-top
import argparse
import time
import json
from random import randint
import datetime
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web

try:
  from hbs_master_3b import hbs_sample_3, init_leds, trigger_led, read_food_res_lvl_sensor, read_food_bowl_lvl_sensor
  from hbs_master_3b import FOOD_LED, WATER_LED, TREAT_LED
except ImportError:
  pass

try:
  from hbs_master_4b import hbs_sample_4, read_dht_sensor
except ImportError:
  pass

# RPi Version
RPI_VERSION = 0

# Initial start of the treat level (in oz.)
TREAT_LVL = 50

# List of user configured feeding times
FEED_TIMES = []
# Amount of food to dispense at automatic feeding (in ounces)
FOOD_AMOUNT_AUTO = []
# Amount of food to dispense at user controlled feeding (in ounces)
FOOD_AMOUNT_GEN = 8
# Flag to determine whether automatic feeding is enabled or not
AUTO_FEED_ENABLED = False

# Websocket Handling
class WSHandler(tornado.websocket.WebSocketHandler):	
  tracker_dist = 0
  
  #enable cross domain origin (idk)
  def check_origin(self, origin):
    return True

  def open(self):
    print("New Tornado Connection Opened")
    self.write_message("Connected to tornado test server")

  def on_close(self):
    print("Tornado Connection Closed")

  def on_message(self, message):
    print("Received:" + message)
    if(message == "get"):
      # Read sensor values
      data = read_sensors(self.tracker_dist)
      json_str = json.dumps(data, default=str)
      # send back
      self.write_message(json_str)
      
      # If automatic feeding is enabled, check if it's time to dispense food
      if AUTO_FEED_ENABLED:
        dispense_food()

      # Update iterators for next loop
      if self.tracker_dist < 50:
        self.tracker_dist += 2
      else:
        self.tracker_dist -= 2
      
    elif ('action' in message):
      d = json.loads(message)
      handle_actions(d)
    elif ('settings' in message):
      handle_settings(message)
    else:
      print("Message received is unknown type")

  def check_origin(self, origin):
    return True

def make_app():
  return tornado.web.Application([
    (r'/ts', WSHandler),
  ])

# Initialize water sensor values and LEDs
def init_system():
  if RPI_VERSION == 3:
    init_leds()

# Dispensing water
def dispense_water():
  print("Dispensing water")
  if RPI_VERSION == 3:
    trigger_led(WATER_LED)

# Dispensing a treat
def dispense_treat():
  global TREAT_LVL
  TREAT_LVL = max(TREAT_LVL-1, 0)
  print("Dispensing treat. Treat level now at {}".format(TREAT_LVL))
  if RPI_VERSION == 3:
    trigger_led(TREAT_LED)

# Check if it is time to automatically dispense food
def dispense_food():
  hour = datetime.datetime.now().hour
  min = datetime.datetime.now().minute

  time = str(hour) + ":" + str(min)
  if time in FEED_TIMES:
    time_idx = FEED_TIMES.index(time)
    print("Automated feeding - dispensing {} oz.".format(FOOD_AMOUNT_AUTO[time_idx]))
    if RPI_VERSION == 3:
        trigger_led(FOOD_LED)

# Get data from sensors and put into a JSON format
def read_sensors(tracker_dist):
  if RPI_VERSION == 3:
    food_res_lvl = read_food_res_lvl_sensor()
    food_bowl_lvl = read_food_bowl_lvl_sensor()
    water_bowl_lvl = randint(40, 60)
    temp = randint(18, 24)
  else:
    food_res_lvl = randint(20,40)
    food_bowl_lvl = randint(3,8)
    water_bowl_lvl, temp = read_dht_sensor()
  treat_res_lvl = TREAT_LVL
  pet_dist = tracker_dist

  sensor_data = {"timestamp" : datetime.datetime.now(),
                 "water_lvl" : water_bowl_lvl,
                 "food_bowl_lvl" : food_bowl_lvl,
                 "food_res_lvl" : food_res_lvl,
                 "treat_lvl" : treat_res_lvl,
                 "pet_dist" : pet_dist,
                 "temp": temp}

  return sensor_data

# Handle actions from the GUI
def handle_actions(msg):
  if msg['action'] == 'empty_water':
    dispense_water()
  elif msg['action'] == 'fill_water':
    print("Filling water bowl")
    if RPI_VERSION == 3:
      trigger_led(WATER_LED)
  elif msg['action'] == 'dispense_food':
    print('Dispensing food')
    if RPI_VERSION == 3:
      trigger_led(FOOD_LED)
  elif msg['action'] == 'dispense_treat':
    dispense_treat()

# Handle settings changes from the GUI
def handle_settings(msg):
  global FEED_TIMES, FOOD_AMOUNT_AUTO, FOOD_AMOUNT_GEN, AUTO_FEED_ENABLED
  d = json.loads(msg)
  print("Setting food dispensing amount to {} oz.".format(d['food_amount_gen']))
  FOOD_AMOUNT_GEN = d['food_amount_gen']
  
  print("Adjusting automatic feeding to {}".format(d['auto_feed']))
  AUTO_FEED_ENABLED = d['auto_feed']
  
  if AUTO_FEED_ENABLED:
    # update feeding schedule and amounts
    print("Adjusting feeding schedule")
    FEED_TIMES.clear()
    FEED_TIMES = d['feed_times']
    print(FEED_TIMES)
    
    print("Setting automatic feeding food amount to {} oz.".format(d['food_amount_auto']))
    FOOD_AMOUNT_AUTO = d['food_amount_auto']
    

def main():
    if RPI_VERSION == 3:
        hbs_sample_3()
    elif RPI_VERSION == 4:
        hbs_sample_4()

    init_system()
    print("Initialized Home Base Station")

    application = make_app()
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)
    print("Starting Server")
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Run pet monitor system')
  parser.add_argument('rpi_version')
  args = parser.parse_args()
  print('RPi version {} specified'.format(args.rpi_version))
  RPI_VERSION = int(args.rpi_version)
  main()

