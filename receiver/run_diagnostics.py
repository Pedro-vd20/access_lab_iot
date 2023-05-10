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

import os
import json
import sys

##########

'''
This file is meant to run analysis on the data provided to determine if there
are any errors on the station sending data
'''

##########

NUM_ARGS = 3
MAX_TEMP = 70
MAX_DISK = 0.85

##########


def check_args(args):
    '''
    Checks the arguments passed and formats them if need be
    '''
    # check number of arguments
    if len(args) < NUM_ARGS + 1:
        raise IndexError('Insufficient arguments. Input path to data file, ' +
                         'path to config file, and whether the file is ' +
                         'diagnositc or not')

    # collect args
    data_path = args[1]
    config_path = args[2]
    is_diag = args[3]

    # check valid args
    if not (os.path.isfile(data_path) and os.path.isfile(config_path)):
        raise FileNotFoundError(f'Could not locate {data_path} or ' +
                                f'{config_path}')

    # check is_diag as boolean
    if is_diag not in ('True', 'False'):
        raise ValueError(f"Could not convert '{is_diag}' to boolean")

    is_diag = (is_diag == 'True')

    return data_path, config_path, is_diag


def check_attr(data, attr, thresh):
    '''
    Checks whether all the values in temp and disk space are under threshhold
    Returns values outside reach
    '''
    # collects all values above threshhold and records respective times and
    # dates
    crit_values = {attr: [], 'date': [], 'time': []}

    # collect values
    for i, val in enumerate(data[attr]):
        if float(val) >= thresh:
            crit_values[attr].append(val)
            crit_values['date'].append(data['date'][i])
            crit_values['time'].append(data['time'][i])

    return crit_values


#########

def main():
    # collect arguments
    data_file, config_file, is_diag = check_args(sys.argv)

    # read file contents
    with open(data_file, 'r') as in_f:
        data = json.load(in_f)

    is_error = False
    errors = {'file': data_file}
    # check diagnostics file
    if is_diag:
        cpu_temp = check_attr(data, 'cpu_temp', MAX_TEMP)
        disk_space = check_attr(data, 'disk_space', MAX_DISK)

        if cpu_temp['cpu_temp']:
            is_error = True
            errors['cpu_temp'] = True
        if disk_space['disk_space']:
            is_error = True
            errors['disk_space'] = True

    # check data file
    else:
        # check against configuration file
        with open(config_file, 'r') as in_f:
            config = json.load(in_f)

        for sensor in data:
            # for gps, check if None
            if sensor == 'date_time_position':
                if None in data[sensor].values():
                    is_error = True
                    errors[sensor] = True
            else:
                # check if less sensors than those in cofig file
                if len(data[sensor]) != config[sensor]:
                    is_error = True
                    errors[f'inconsistent_num_{sensor}'] = True

                # check if any sensor is None
                if None in data[sensor]:
                    is_error = True
                    errors[f'faulty_sensor_{sensor}'] = True

                # check if individual sensors have their own in-built
                # diagnostics
                for s in data[sensor]:
                    if s is None:
                        continue

                    # currently not implemented
                    if 'diagnostics' in s:
                        for key in s['diagnostics']:
                            print(s['diagnostics'][key])

                # check drift between sensors tbd

    if is_error:
        print(errors)


if __name__ == '__main__':
    main()
