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
from sensors import *
from modules import log


# all this file will do is attempt to request measurements from all sensors
# if it crashes at any point, it will log failure and let the user know
def main():
    try:
        print('Testing Sensors')
        for i in range(len(sensors)):
            print('Testing', i)
            print(sensors[i].measure())
        print()


        print('Testing GPS')
        print(gps.fix())
        print()

    except Exception as e:
        print('Error connecting to sensors')
        log('Testing sensors failed, must check connection')
        raise(e)


if __name__ == '__main__':
    main()
