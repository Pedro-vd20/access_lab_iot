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
        'memory': [],
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
            diagnostics['memory'].append(mem)
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
