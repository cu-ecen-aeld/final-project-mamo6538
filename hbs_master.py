import RPi.GPIO as GPIO
import time
from gpiozero import MCP3008
import json
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import aws_keys
from random import randint
import datetime
import boto3
from picamera2 import Picamera2, Preview

# Instantiate AWS clients for S3 and SQS
s3 = boto3.client('s3', region_name='us-east-1', aws_access_key_id = aws_keys.ACCESS_KEY, aws_secret_access_key = aws_keys.SECRET_ACCESS_KEY)
sqs_client = boto3.client('sqs', region_name='us-east-1', aws_access_key_id = aws_keys.ACCESS_KEY, aws_secret_access_key = aws_keys.SECRET_ACCESS_KEY)

# LED to indicate when the food is being dispensed
FOOD_LED  = 27
# LED to indicate when the water bowl is being cleaned
WATER_LED = 22
# LED to indicate when treat is being dispensed
TREAT_LED = 4

# Water bowl sensor
water_bowl_sens = MCP3008(0)
# Maximum water level reading (100% equivalent)
WATER_HIGH_LVL = 1.1
# Food bowl sensor
food_bowl_sens = MCP3008(2)
# Food reservoir sensor
food_res_sens = MCP3008(1)
# Max weight of food reservoir (in lbs)
FOOD_RES_MAX_WEIGHT = 4
# Max weight of food bowl (in oz.)
FOOD_BOWL_MAX_WEIGHT = 8
# Initial start of the treat level (in oz.)
TREAT_LVL = 50

# MQTT client for pushing sensor data to AWS
dataMQTTClient = AWSIoTMQTTClient("hbs_data")

# List of user configured feeding times
FEED_TIMES = []
# Amount of food to dispense at automatic feeding (in ounces)
FOOD_AMOUNT_AUTO = []
# Amount of food to dispense at user controlled feeding (in ounces)
FOOD_AMOUNT_GEN = 8
# Flag to determine whether automatic feeding is enabled or not
AUTO_FEED_ENABLED = False

# Camera module
pi_cam = Picamera2()

# Get URL of the desired SQS queue
def get_queue_url():
  rsp = sqs_client.get_queue_url(QueueName="iot23_kabi_petmonitor_sqs")
  print(rsp["QueueUrl"])
  return rsp["QueueUrl"]
  
# Receive messages from settings/action SQS
def receive_msg(queue):
  rsp = sqs_client.receive_message(QueueUrl = queue,
                                   MaxNumberOfMessages=5,
                                   WaitTimeSeconds=5)
  print("Messages received: {}".format(len(rsp.get('Messages', []))))
  return rsp

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

# Read data from water sensor
def read_water_sensor():
  lvl = water_bowl_sens.value
  percent_lvl = (lvl / WATER_HIGH_LVL) * 100.0
  return round(percent_lvl, 2)

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

# Initialize water sensor values, camera, and MQTT
def init_system():
  global WATER_HIGH_LVL

  init_leds()

  WATER_HIGH_LVL = water_bowl_sens.value
  print("Init water high lvl {}".format(WATER_HIGH_LVL))
  
  camera_config = pi_cam.create_preview_configuration()
  pi_cam.configure(camera_config)
  pi_cam.start()
  
  dataMQTTClient.configureEndpoint(aws_keys.AWS_ENDPOINT,8883)
  dataMQTTClient.configureCredentials(aws_keys.AWS_CA1,
                                      aws_keys.AWS_PRIVATE_KEY,
   
                                      aws_keys.AWS_CERT)

  dataMQTTClient.configureOfflinePublishQueueing(-1)
  dataMQTTClient.configureDrainingFrequency(2)  # 2 Hz
  dataMQTTClient.configureConnectDisconnectTimeout(10) # 10 sec
  dataMQTTClient.configureMQTTOperationTimeout(5) # 5 sec
  dataMQTTClient.connect()

# Get data from sensors and put into a JSON format
def read_sensors(tracker_dist):
  water_bowl_lvl = read_water_sensor()
  food_res_lvl = read_food_res_lvl_sensor()
  food_bowl_lvl = read_food_bowl_lvl_sensor()
  #water_bowl_lvl = randint(40, 60)
  #food_res_lvl = randint(20,40)
  #food_bowl_lvl = randint(3,8)
  treat_res_lvl = TREAT_LVL
  pet_dist = tracker_dist
  
  sensor_data = {"timestamp" : datetime.datetime.now(),
                 "water_lvl" : water_bowl_lvl,
                 "food_bowl_lvl" : food_bowl_lvl,
                 "food_res_lvl" : food_res_lvl,
                 "treat_lvl" : treat_res_lvl,
                 "pet_dist" : pet_dist}
  
  return sensor_data

# Handle actions from the GUI
def handle_actions(msg):
  global TREAT_LVL

  if msg['action'] == 'empty_water':
    print("Emptying water bowl")
    trigger_led(WATER_LED)
  elif msg['action'] == 'fill_water':
    print("Filling water bowl")
    trigger_led(WATER_LED)
  elif msg['action'] == 'dispense_food':
    print("Dispensing food")
    trigger_led(FOOD_LED)
  elif msg['action'] == 'dispense_treat':
    print('Dispensing treat')
    if TREAT_LVL > 0:
      TREAT_LVL = TREAT_LVL - 1
    trigger_led(TREAT_LED)

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

# Process messages from the GUIs and handle as needed
def process_msgs(rsp, url):
  for msg in rsp.get("Messages", []):
    msg_body = msg["Body"]
    json_msg = json.loads(msg_body)
    if 'action' in json_msg:
      handle_actions(json_msg)
    if 'settings' in json_msg:
      handle_settings(json_msg['settings'])

    sqs_client.delete_message(QueueUrl=url, ReceiptHandle=msg['ReceiptHandle'])

# Check if it is time to automatically dispense food
def dispense_food():
  hour = datetime.datetime.now().hour
  min = datetime.datetime.now().minute

  time = str(hour) + ":" + str(min)
  if time in FEED_TIMES:
    time_idx = FEED_TIMES.index(time)
    trigger_led(FOOD_LED)
    print("Automated feeding - dispensing {} oz.".format(FOOD_AMOUNT_AUTO[time_idx]))


def main():
  tracker_dist = 0
  init_system()
  print("Initialized Home Base Station")

  gui_sqs = get_queue_url()

  while True:
    # Read sensor values
    data = read_sensors(tracker_dist)
    json_str = json.dumps(data, default=str)
    print(json_str)

    # Get updated user actions from AWS SQS if any
    gui_msgs = receive_msg(gui_sqs)    
    process_msgs(gui_msgs, gui_sqs)

    # Push data to MQTT
    dataMQTTClient.publish(topic="hbs_data", QoS=1, payload=json_str)
    
    # If automatic feeding is enabled, check if it's time to dispense food
    if AUTO_FEED_ENABLED:
      dispense_food()
    
    # Update iterators for next loop
    if tracker_dist < 50:
      tracker_dist += 2
    else:
       tracker_dist -= 2

    # Capture camera image & upload to AWS bucket
    pi_cam.capture_file("test.jpg")
    s3.upload_file('./test.jpg', 'iot23.kabi.bucket', 'test.jpg')

    time.sleep(10)
  
  
if __name__ == "__main__":
  main()
