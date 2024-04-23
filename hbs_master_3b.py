from gpiozero import MCP3008
import RPi.GPIO as GPIO
import time

# LED to indicate when the food is being dispensed
FOOD_LED  = 27
# LED to indicate when the water bowl is being cleaned
WATER_LED = 22
# LED to indicate when treat is being dispensed
TREAT_LED = 4

# Max weight of food reservoir (in lbs)
FOOD_RES_MAX_WEIGHT = 4
# Max weight of food bowl (in oz.)
FOOD_BOWL_MAX_WEIGHT = 8

# Food bowl sensor
food_bowl_sens = MCP3008(channel=0, clock_pin=11, mosi_pin=10, miso_pin=9, select_pin=8)
# Food reservoir sensor
food_res_sens = MCP3008(channel=1, clock_pin=11, mosi_pin=10, miso_pin=9, select_pin=8)

# Initialize LEDs
def init_leds():
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(FOOD_LED, GPIO.OUT)
  GPIO.setup(WATER_LED, GPIO.OUT)
  GPIO.setup(TREAT_LED, GPIO.OUT)

  GPIO.output(FOOD_LED, GPIO.LOW)
  GPIO.output(WATER_LED, GPIO.LOW)
  GPIO.output(TREAT_LED, GPIO.LOW)

# Trigger the setting of a given LED
def trigger_led(led):
  GPIO.output(led, GPIO.HIGH)
  time.sleep(2)
  GPIO.output(led, GPIO.LOW)

# Read data from food reservoir pressure sensor
def read_food_res_lvl_sensor():
  lvl = food_res_sens.value
  res_weight = (lvl / 1.0) * FOOD_RES_MAX_WEIGHT
  return round(res_weight, 2)

# Read data from food bowl pressure sensor
def read_food_bowl_lvl_sensor():
  lvl = food_bowl_sens.value
  bowl_weight = (lvl / 1.0) * FOOD_BOWL_MAX_WEIGHT
  return round(bowl_weight, 2)

def hbs_sample_3():
    print('test 3')