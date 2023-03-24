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

import time
import json
import os
import station_id as station
from werkzeug.utils import secure_filename
import packages.modules as modules

##########

'''
Collect status information on the RPi every 24 hours
Collects disk space and cpu temperature
'''

##########

# constants

SAMPLING_INTERVAL = 86400  # in seconds
DATA_SAMPLING_INTERVAL = 600
DIAG_FILE = os.path.join(modules.HOME, f'station{station.station_num}' +
                         '_diagnostics.txt')
TIME_FILE = os.path.join(modules.HOME, 'time.txt')


##########


def wait_for_files() -> None:
    '''
    Diagnostics needs data collection to create these files before running.
    This loop waits in case they haven't been created yet
    '''

    # loop until files exist
    while not (os.path.isfile(DIAG_FILE) and os.path.isfile(TIME_FILE)):
        modules.log('No diagnostics to send')
        time.sleep(600)


def get_date_time() -> tuple:
    '''
    Since 2 scripts can't use the gps and data collection needs it, accurate
    date/time info is stored by data collection in a temp file
    @return 2-tuple with date and time string variables
    '''

    # stores these in time_f for us to use
    with open(TIME_FILE, 'r') as time_f:
        curr_time = time_f.readline().strip()
        curr_date = time_f.readline().strip()

    return curr_date, curr_time


def read_groups() -> list:
    '''
    Collects all the groups of data from the daig file written by
    data_collection
    A single entry in diag is a group of lines, different entries are separated
    by an empty line
    This methods creates a 2-d list where each index is a group and each inner
    array are the lines of the group
    @return 2-d array of groups
    '''

    # read the contents of diag_file to send and format
    with open(DIAG_FILE, 'r') as in_f:
        # read groups of lines
        groups = []
        temp = []

        for line in in_f:
            line = line.strip()

            # current group of data is finished, add it to groups
            if line == '' and len(temp) != 0:
                groups.append(temp)
                temp = []
            # current line is part of bigger group, append to temp
            elif line != 0:
                temp.append(line.strip())

    return groups


def process_groups(groups: list) -> dict:
    '''
    Process the diagnostics groups into the diagnostics dictionary
    Figures out what kind of diagnostic it is. A group can either be
    describing an error or a cpu temp / disk space collection
    @param groups 2-d list of diagnostics
    @return diag dictionary to format data into. Must fill in with the info
    '''

    # data structure to fill in and send to server
    diag = {
        'id': station.secret,
        'cpu_temp': [],
        'disk_space': [],
        'time': [],
        'date': [],
        'errors': {
        }
    }

    # process each line group
    for group in groups:

        # check if group describes an error
        if len(group) == 3:  # group is an error
            time_date = group[0].strip().split(' ')
            error_name = group[1].strip()
            error = group[2].strip()

            # fill in data
            diag['errors'][error_name] = {
                'time': time_date[1],
                'date': time_date[0],
                'error': error
            }

        elif len(group) == 5:  # group is a disk/cpu data
            time_date = group[0].strip().split(' ')
            cpu = group[2].strip()
            disk = group[4].strip()

            # fill in data
            diag['cpu_temp'].append(cpu)
            diag['disk_space'].append(disk)
            diag['time'].append(time_date[1])
            diag['date'].append(time_date[0])

    return diag


def save_data(date: str, time: str, data: dict, is_diag: bool = False) -> None:
    '''
    Save date collected by the sensors into a file and call sender to send it
    @param date Date data was collected, to be used in file name
    @param time Time data was collected, to be used in file name
    @param data Dict to save
    @param is_diag states if current data is from a diagnostics or not
        (affects file naming)
    '''

    # construct secure file name (if is diag or not)
    end_of_f_name = '_diagnostics.json' if is_diag else '.json'
    f_name = secure_filename(f'station{station.station_num}_{date}T{time}Z' +
                             end_of_f_name)

    # dump data into file
    with open(os.path.join(modules.HOME, 'data_logs', f_name), 'w') as f:
        json.dump(data, f, indent=4)

    # send the file to server
    os.system(f'python3 {os.path.join(modules.HOME, "sender.py")}')


##########


# sleep some time to let data_collection begin
time.sleep(20)


def main():

    while True:
        start_measurement_cycle = time.time()

        # check if necessary files for data collection are available
        wait_for_files()

        curr_date, curr_time = get_date_time()

        # read the diagnostics file and collect groups of data reported by
        # data_collection
        diag_groups = read_groups()

        # Check again if file is empty, sleep for data_collection to fill
        # diagnostics
        if len(diag_groups) == 0:
            modules.log('No diagnotics to send')
            time.sleep(600)
            continue

        # process each group into the diagnostics dictionary
        diagnostics = process_groups(diag_groups)

        # dump file into data_logs
        save_data(curr_date, curr_time, diagnostics, is_diag=True)

        # reset contents of diag_file
        open(DIAG_FILE, 'w').close()

        # sleep until next day
        elapsed = time.time() - start_measurement_cycle
        time.sleep(SAMPLING_INTERVAL - elapsed)


if __name__ == '__main__':
    main()
