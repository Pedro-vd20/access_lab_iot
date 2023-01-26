'''

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


import sensors as sens
import packages.modules as modules
import json
import os


# all this file will do is attempt to request measurements from all sensors
# if it crashes at any point, it will log failure and let the user know
def main():
    try:
        print('Testing Sensors')
        for i in range(len(sens.sensors)):
            print('Testing', i)
            print(sens.sensors[i].measure())
        print()


        print('Testing GPS')
        print(sens.gps.fix())
        print()

    except Exception as e:
        print('Error connecting to sensors')
        modules.log('Testing sensors failed, must check connection')
        raise(e)

    # create config file
    sensors_dict = {}
    for sensor in sens.sensors:
        sensors_dict[sensor.SENSOR] = sensors_dict.get(sensor.SENSOR, 0) + 1

    with open(os.path.join(modules.HOME, 'station.config'), 'w') as f:
        json.dump(sensors_dict, f, indent=4)

    return 0


if __name__ == '__main__':
    main()
