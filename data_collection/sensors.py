import ACCESS_station_lib as access
import board

try:
    gps = access.GPSbeseecherGPIO() # only 1 GPS
except:
    gps = access.ErrorBeseecher('Error initializing GPS at boot')

pm = []
ports = ['/dev/ttyAMA0', '/dev/ttyAMA1']

for i in range(2):
    try:
        pm.append(access.NEXTPMbeseecher(port=ports[i]))
    except Exception as e:
        pm.append(access.ErrorBeseecher(str(e)))

i2c = board.I2C()

air_sens = []

try:
    air_sens.append(access.BME280beseecher(i2c=i2c))
except Exception as e:
    error_msg = str(e) + ' (bme280)'
    air_sens.append(access.ErrorBeseecher(error_msg))
try:
    air_sens.append(access.MS8607beseecher(i2c=i2c))
except Exception as e:
    error_msg = str(e) + ' (ms8607)'
    air_sens.append(access.ErrorBeseecher(error_msg))


