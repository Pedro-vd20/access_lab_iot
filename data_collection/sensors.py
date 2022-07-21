import ACCESS_station_lib as access
import board

# with the exception of the gps, for all other sensors, 
# even if there is only one connected to the pi, please 
# keep them in a list. All other modules assume they will
# be in a list, wether as a single-item list, or as 
# multiple sensors

try:
    gps = access.GPSbeseecherGPIO() # only 1 GPS
except:
    gps = access.ErrorBeseecher('Error initializing GPS at boot')

pm = []

# add nextPM
try:
    pm.append(access.NEXTPMbeseecher())
except Exception as e:
    pm.append(access.ErrorBeseecher(str(e)))

# add sps30
try:
    pm.append(access.SPS30beseecher())
except Exception as e:
    pm.append(access.ErrorBeseecher(str(e)))


i2c = board.I2C()

air_sens = []

try:
    air_sens.append(access.BME280beseecher(i2c=i2c))
except Exception as e:
    error_msg = str(e) + ' (bme280)'
    air_sens.append(access.ErrorBeseecher(error_msg))

