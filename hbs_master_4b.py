import re

def read_dht_sensor():
    t_sensor_fd = open("/dev/aht20")
    # Expected data format is "temp:#C, humid:#"
    sensor_reading = t_sensor_fd.read()
    print(sensor_reading)
    data = re.findall(r'\d+', sensor_reading)
    # return water level, temp
    return int(data[1]), int(data[0])

def hbs_sample_4():
    print('test 4')