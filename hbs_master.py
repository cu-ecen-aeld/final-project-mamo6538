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
    print("Received:" + message)
    if(message == "get"):
      self.write_message(str(self.testVal))
    elif ('action' in message):
      handle_actions(message)
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
  global RPI_VERSION
  if RPI_VERSION == 3:
    init_leds()

# Dispensing water
def dispense_water():
  global RPI_VERSION
  print("Dispensing water")
  if RPI_VERSION == 3:
    trigger_led(WATER_LED)

# Dispensing a treat
def dispense_treat():
  global TREAT_LVL, RPI_VERSION
  TREAT_LVL = max(TREAT_LVL-1, 0)
  print("Dispensing treat. Treat level now at {}".format(TREAT_LVL))
  if RPI_VERSION == 3:
    trigger_led(TREAT_LED)

# Check if it is time to automatically dispense food
def dispense_food():
  global RPI_VERSION
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
  global RPI_VERSION
  if RPI_VERSION == 3:
    food_res_lvl = read_food_res_lvl_sensor()
    food_bowl_lvl = read_food_bowl_lvl_sensor()
    water_bowl_lvl = randint(40, 60)
    temp = randint(65, 75)
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
  global RPI_VERSION
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
  if "feed_times" in msg:
    print("Adjusting feeding schedule")
    FEED_TIMES.clear()
    FEED_TIMES = msg['feed_times']
    print(FEED_TIMES)
  if "food_amount_auto" in msg:
    print("Setting automatic feeding food amount to {} oz.".format(msg['food_amount_auto']))
    FOOD_AMOUNT_AUTO = msg['food_amount_auto']
  if "food_amount_gen" in msg:
    print("Setting food dispensing amount to {} oz.".format(msg['food_amount_gen']))
    FOOD_AMOUNT_GEN = msg['food_amount_gen']
  if "auto_feed" in msg:
    print("Adjusting automatic feeding to {}".format(msg['auto_feed']))
    AUTO_FEED_ENABLED = msg['auto_feed']

def main():
    global RPI_VERSION
    if RPI_VERSION == 3:
        hbs_sample_3()
    elif RPI_VERSION == 4:
        hbs_sample_4()

    tracker_dist = 0
    init_system()
    print("Initialized Home Base Station")

    application = make_app()
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)
    tornado.ioloop.IOLoop.current().start()

    ### TODO - Need to tie the sensor reading and auto feed checking/distance updating to server ###
    while True:
        # Read sensor values
        data = read_sensors(rpi_version, tracker_dist)
        json_str = json.dumps(data, default=str)
        print(json_str)
        #TODO - push sensor readings so gui is updated?

        # If automatic feeding is enabled, check if it's time to dispense food
        if AUTO_FEED_ENABLED:
            dispense_food(rpi_version)

        # Update iterators for next loop
        if tracker_dist < 50:
            tracker_dist += 2
        else:
            tracker_dist -= 2

        time.sleep(10)

if __name__ == "__main__":
  global RPI_VERSION
  parser = argparse.ArgumentParser(description='Run pet monitor system')
  parser.add_argument('rpi_version')
  args = parser.parse_args()
  print('RPi version {} specified'.format(args.rpi_version))
  RPI_VERSION = int(args.rpi_version)
  main()