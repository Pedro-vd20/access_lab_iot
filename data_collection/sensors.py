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
        pm.append(access.ErrorBeseecher('particulate_matter', 'nextpm', str(e)))

i2c = board.I2C()

air_sens = []

try:
    air_sens.append(access.BME280beseecher(i2c=i2c))
except Exception as e:
    error_msg = str(e) + ' (bme280)'
    air_sens.append(access.ErrorBeseecher('air_sensor', 'bme280', error_msg))
try:
    air_sens.append(access.MS8607beseecher(i2c=i2c))
except Exception as e:
    error_msg = str(e) + ' (ms8607)'
    air_sens.append(access.ErrorBeseecher('air_sensor', 'ms8607', error_msg))


