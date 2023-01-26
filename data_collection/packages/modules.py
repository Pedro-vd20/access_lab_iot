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

import os
import datetime

#---------

''' 
shared code for multiple files
'''

#----------

HOME = '/home/pi/'
PATH = '/home/pi/boot/'
STATE = 'state.txt'

#----------

# makes running console commands easier
def run(comm):
    os.system(comm)

'''
Log information for later debugging
Collects timestamp of log 
'''
def log(msg):
    # get current time
    now = datetime.datetime.now() 
    year = now.year
    month = now.month

    with open(f'{HOME}logs/{year}_{month}_logs.txt', 'a') as f:
        f.write(now.strftime('[%Y-%m-%d %H:%M:%S] '))
        f.write(msg + '\n')

'''
Write current boot state to file
'''
def write_state(num):
    with open(f'{PATH}{STATE}', 'w') as f:
        f.write(str(num))


    
