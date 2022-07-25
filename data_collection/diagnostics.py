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

import time
import datetime
import json
import sys
from shutil import disk_usage
from gpiozero import CPUTemperature
from station_id import *
from werkzeug.utils import secure_filename
from modules import *

SamplingInterval = 86400 #in seconds
MAX_SAMPLES = 1

#------------------------------------------------

nerror = 0

time.sleep(20)

while True:
    start_measurement_cycle = time.time()

    diag_file = HOME + 'station' + station_num + '_diagnostics.txt'

    try:
        f = open(diag_file, 'r')
    except:
        log('No diagnostics to send')
        time.sleep(600)
        continue

    # read groups of lines
    lines = []
    temp = []
    for line in f:
        line = line.strip()
        if line == '' and len(temp) != 0:
            lines.append(temp)
            temp = []
        elif line != 0:
            temp.append(line.strip())
    f.close()

    if len(lines) == 0:
        log('No diagnotics to send')
        time.sleep(600)
        continue

    diagnostics = {
        'id': secret,
        'cpu_temp': [],
        'disk_space': [],
        'time': [],
        'date': [],
        'errors': {
            
        }
    }

    # process each line group
    for group in lines:
        is_empty = False
        if len(group) == 3: # group is an error    
            time_date = group[0].strip().split(' ')
            error_name = group[1].strip()
            error = group[2].strip()

            diagnostics['errors'][error_name] = {
                'time': time_date[1],
                'date': time_date[0],
                'error': error
            }
        elif len(group) == 5: # group is a memory/cpu data
            time_date = group[0].strip().split(' ')
            cpu = group[2].strip()
            mem = group[4].strip()

            diagnostics['cpu_temp'].append(cpu)
            diagnostics['disk_space'].append(mem)
            diagnostics['time'].append(time_date[1])
            diagnostics['date'].append(time_date[0])

    # get time
    try:
        f = open(HOME + 'time.txt', 'r')
    except:
        time.sleep(600) # wait for first round of data collection
        continue
    curr_time = f.readline().strip()
    curr_date = f.readline().strip()

    f_name = secure_filename('station' + station_num + '_' + curr_date + 'T' + curr_time + 'Z_diagnostics.json')
    with open(HOME + 'logs/' + f_name, 'w') as f:
        json.dump(diagnostics, f, indent=4)
    
    f = open(diag_file, 'w')
    f.close()

    elapsed = time.time() - start_measurement_cycle
    time.sleep(SamplingInterval - elapsed)
