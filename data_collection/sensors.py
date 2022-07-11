import ACCESS_station_lib as access
import board

try:
    gps = access.GPSbeseecherGPIO() # only 1 GPS
except:
    gps = None

pm = []

try:
    pm.append(access.NEXTPMbeseecher())
except:
    pm.append(None)
try:
    pm.append(access.NEXTPMbeseecher(port='/dev/ttyAMA1'))
except:
    pm.append(None)


i2c = board.I2C()


air_sens = []

try:
    air_sens.append(access.BME280beseecher(i2c=i2c))
except:
    air_sens.append(None)
try:
    air_sens.append(access.MS8607beseecher(i2c=i2c))
except:
    air_sens.append(None)


