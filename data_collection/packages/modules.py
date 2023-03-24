'''

Copyright (C) 2022 Francesco Paparella, Pedro Velasquez

This file is part of "ACCESS IOT Stations".

"ACCESS IOT Stations" is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

"ACCESS IOT Stations" is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
details.

You should have received a copy of the GNU General Public License along with
"ACCESS IOT Stations". If not, see <https://www.gnu.org/licenses/>.

'''

##########

import os
import datetime

##########

'''
Shared code for multiple files
This module contains common functions used by data_collection and setup
'''

##########

# constants declarations

HOME = '/home/pi/'
PATH = '/home/pi/boot/'
STATE = 'state.txt'


##########


def run(comm: str) -> None:
    '''
    Makes running terminal commands easier
    @param comm Ful command to run
    '''
    os.system(comm)


def log(msg: str) -> None:
    '''
    Log information for later debugging
    Collects timestamp of log
    @param msg String to write into log file
    '''

    # get current time
    now = datetime.datetime.now()
    year = now.year
    month = now.month

    # append log
    with open(os.path.join(HOME, 'logs', f'{year}_{month}_logs.txt'),
              'a') as out_f:
        out_f.write(now.strftime('[%Y-%m-%d %H:%M:%S] '))
        out_f.write(msg + '\n')


def write_state(num: int) -> None:
    '''
    Write current boot state to file
    @param num Current state
    '''
    with open(os.path.join(PATH, STATE), 'w') as out_f:
        out_f.write(str(num))
