import argparse
from hbs_master_3b import hbs_sample_3, init_leds, trigger_led, read_food_res_lvl_sensor, read_food_bowl_lvl_sensor
from hbs_master_4b import hbs_sample_4, read_water_sensor
import time
import json
from random import randint
import datetime

# Maximum water level reading (100% equivalent)
WATER_HIGH_LVL = 1.1
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

# Initialize water sensor values and LEDs
def init_system(rpi_version):
  global WATER_HIGH_LVL
  if rpi_version == 3:
    init_leds()
    WATER_HIGH_LVL = 1.1
  else:
    WATER_HIGH_LVL = read_water_sensor()
  print("Init water high lvl {}".format(WATER_HIGH_LVL))

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
  else:
    food_res_lvl = randint(20,40)
    food_bowl_lvl = randint(3,8)
    water_bowl_lvl = read_water_sensor()
  treat_res_lvl = TREAT_LVL
  pet_dist = tracker_dist
  
  sensor_data = {"timestamp" : datetime.datetime.now(),
                 "water_lvl" : water_bowl_lvl,
                 "food_bowl_lvl" : food_bowl_lvl,
                 "food_res_lvl" : food_res_lvl,
                 "treat_lvl" : treat_res_lvl,
                 "pet_dist" : pet_dist}
  
  return sensor_data

def main(rpi_version):
    if rpi_version == 3:
        hbs_sample_3()
    elif rpi_version == 4:
        hbs_sample_4()
    
    tracker_dist = 0
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

        time.sleep(10)

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Run pet monitor system')
  parser.add_argument('rpi_version')
  args = parser.parse_args()
  print('RPi version {} specified'.format(args.rpi_version))
  main(int(args.rpi_version))