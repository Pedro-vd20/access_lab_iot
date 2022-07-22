'''
ACCESS Lab, hereby disclaims all copyright interest in the program “ACCESS IOT 
Stations” (which collects air and climate data) written by Francesco Paparella, 
Pedro Velasquez.

Copyright (C) 2022 Francesco Paparella, Pedro Velasquez

This file is part of "ACCESS IOT Stations".

"ACCESS IOT Stations" is free software: you can redistribute it and/or modify it under the 
terms of the GNU General Public License as published by the Free Software 
Foundation, either version 3 of the License, or (at your option) any later 
version.

"ACCESS IOT Stations" is distributed in the hope that it will be useful, but WITHOUT ANY 
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR 
A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with 
"ACCESS IOT Stations". If not, see <https://www.gnu.org/licenses/>.

'''

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

