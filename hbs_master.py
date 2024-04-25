import argparse
from hbs_master_3b import hbs_sample_3, init_leds, trigger_led, read_food_res_lvl_sensor, read_food_bowl_lvl_sensor
from hbs_master_3b import FOOD_LED, WATER_LED, TREAT_LED
from hbs_master_4b import hbs_sample_4, read_dht_sensor
import time
import json
from random import randint
import datetime

# Initial start of the treat level (in oz.)
TREAT_LVL = 50

# List of user configured feeding times
FEED_TIMES = ['00:01', '00:02', '00:05']
# Amount of food to dispense at automatic feeding (in ounces)
FOOD_AMOUNT_AUTO = ['8', '4', '7']
# Flag to determine whether automatic feeding is enabled or not
AUTO_FEED_ENABLED = True

# Initialize water sensor values and LEDs
def init_system(rpi_version):
  if rpi_version == 3:
    init_leds()

# Dispensing water
def dispense_water(rpi_version):
  if rpi_version == 3:
    trigger_led(WATER_LED)
  print("Dispensing water")

# Dispensing a treat
def dispense_treat(rpi_version):
  global TREAT_LVL
  if rpi_version == 3:
    trigger_led(TREAT_LED)
  TREAT_LVL = max(TREAT_LVL-1, 0)
  print("Dispensing treat. Treat level at {}".format(TREAT_LVL))

# Check if it is time to automatically dispense food
def dispense_food(rpi_version):
  hour = datetime.datetime.now().hour
  min = datetime.datetime.now().minute

  time = str(hour) + ":" + str(min)
  if time in FEED_TIMES:
    time_idx = FEED_TIMES.index(time)
    if rpi_version == 3:
        trigger_led(FOOD_LED)
    print("Automated feeding - dispensing {} oz.".format(FOOD_AMOUNT_AUTO[time_idx]))

# Get data from sensors and put into a JSON format
def read_sensors(rpi_version, tracker_dist):
  if rpi_version == 3:
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

def main(rpi_version):
    if rpi_version == 3:
        hbs_sample_3()
    elif rpi_version == 4:
        hbs_sample_4()
    
    tracker_dist = 0
    iter = 0
    init_system(rpi_version)
    print("Initialized Home Base Station")

    while True:
        # Read sensor values
        data = read_sensors(rpi_version, tracker_dist)
        json_str = json.dumps(data, default=str)
        print(json_str)
        
        # If automatic feeding is enabled, check if it's time to dispense food
        if AUTO_FEED_ENABLED:
            dispense_food(rpi_version)
        
        # Update iterators for next loop
        if tracker_dist < 50:
            tracker_dist += 2
        else:
            tracker_dist -= 2

        # Simulate dispensing a treat
        if (iter % 15 == 0):
          dispense_treat(rpi_version)

        # Simulate dispensing water
        if (iter % 10 == 0):
          dispense_water(rpi_version)

        time.sleep(10)

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Run pet monitor system')
  parser.add_argument('rpi_version')
  args = parser.parse_args()
  print('RPi version {} specified'.format(args.rpi_version))
  main(int(args.rpi_version))