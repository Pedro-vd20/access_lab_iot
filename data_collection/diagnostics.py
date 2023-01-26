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

import time
import json
import os
import sys
import station_id as station
from werkzeug.utils import secure_filename
import packages.modules as modules

#----------

'''
Collect status information on the RPi every 24 hours
Collects disk space and cpu temperature
'''

#---------- 

SAMPLING_INTERVAL = 86400 #in seconds

#----------

# sleep some time to let data_collection begin
time.sleep(20)

def main():
    diag_file = os.path.join(modules.HOME, f'station{station.station_num}' + \
        '_diagnostics.txt')
    time_file = os.path.join(modules.HOME, 'time.txt')

    while True:
        start_measurement_cycle = time.time()

        # check if diag file exists (regularly filled by data_collection.py)
        if not (os.path.isfile(diag_file) and os.path.isfile(time_file)):
            modules.log('No diagnostics to send')
            time.sleep(600)
            continue

        # read time
        # data_collection uses accurate, timestamps from GPS
        # stores these in time_f for us to use
        with open(time_file, 'r') as time_f:
            curr_time = time_f.readline().strip()
            curr_date = time_f.readline().strip()

        # read the contents of diag_file to send and format
        with open(diag_file, 'r') as in_f:
            # read groups of lines
            lines = []
            temp = []

            for line in in_f:
                line = line.strip()
                
                # current group of data is finished, add it to lines
                if line == '' and len(temp) != 0:
                    lines.append(temp)
                    temp = []
                # current line is part of bigger group, append to temp
                elif line != 0:
                    temp.append(line.strip())
        
        # Check again if file is empty, sleep for data_collection to fill diagnostics
        if len(lines) == 0:
            modules.log('No diagnotics to send')
            time.sleep(600)
            continue

        # data structure to fill in and send to server
        diagnostics = {
            'id': station.secret,
            'cpu_temp': [],
            'disk_space': [],
            'time': [],
            'date': [],
            'errors': {
                
            }
        }

        # process each line group
        for group in lines:

            # THIS FIRST OPTION IN THE IF IS CURRENTLY DISABLED, NEVER WILL RUN
            if len(group) == 3: # group is an error    
                time_date = group[0].strip().split(' ')
                error_name = group[1].strip()
                error = group[2].strip()

                diagnostics['errors'][error_name] = {
                    'time': time_date[1],
                    'date': time_date[0],
                    'error': error
                }
            elif len(group) == 5: # group is a disk/cpu data
                time_date = group[0].strip().split(' ')
                cpu = group[2].strip()
                disk = group[4].strip()

                diagnostics['cpu_temp'].append(cpu)
                diagnostics['disk_space'].append(disk)
                diagnostics['time'].append(time_date[1])
                diagnostics['date'].append(time_date[0])

        # dump file into data_logs for sender to handle later
        f_name = secure_filename(f'station{station.station_num}_{curr_date}T' + \
            f'{curr_time}Z_diagnostics.json')
        with open(os.path.join(modules.HOME, 'data_logs/', f_name), 'w') as out_f:
            json.dump(diagnostics, out_f, indent=4)
        
        # reset contents of diag_file
        open(diag_file, 'w').close()

        # sleep until next day
        elapsed = time.time() - start_measurement_cycle
        time.sleep(SAMPLING_INTERVAL - elapsed)


if __name__ == '__main__':
    main()
