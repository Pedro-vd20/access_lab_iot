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
from ACCESS_station_lib import *
from sensors import *
from shutil import disk_usage
from gpiozero import CPUTemperature
from station_id import *
from modules import *
from werkzeug.utils import secure_filename

SamplingInterval = 600 #in seconds
MAX_SAMPLES = 1

#------------------------------------------------

##
# writes an occured error into the diagnostics file located at /home/pi/
# @param error_name: error type (air sensor, cpu temperature, exception...)
# @param error: string info describing error
# appends errors to file until diagnostics sends them
def write_diag(error_name, error):
    f = open(f'{HOME}station{station_num}_diagnostics.txt', 'a+')
    
    # timestamp data
    now = datetime.datetime.now()
    f.write(now.strftime('%Y-%m-%d %H:%M:%S'))
    f.write('\n')

    # clean up error
    error = error.replace('\n', ' ')
    error = error.replace('\r', '')
    error = error.replace('\t', ' ')
    while '  ' in error:
        error = error.replace('  ', ' ')

    f.write(str(error_name) + '\n')
    f.write(str(error))
    f.write('\n\n')
    f.close()

##
# writes the cpu temperature and disk space in use into the diagnostic file
# the file is located in /home/pi/
def write_temp_mem(temp, mem):
    f = open(f'{HOME}station{station_num}_diagnostics.txt', 'a+')
    
    # timestamp data
    now = datetime.datetime.now()
    f.write(now.strftime('%Y-%m-%d %H:%M:%S'))
    f.write('\n')

    # write error info
    f.write('cpu\n')
    f.write(str(temp))
    f.write('\nmemory\n')
    f.write(str(mem))
    f.write('\n\n')
    f.close()

#-----------------------------------------------
nerror = 0

send_diag = False

while True:
    # collect start time
    start_measurement_cycle = time.time()
    
    data_to_save = {}
    sensor_indeces = {} # tracks indeces for each sensor type
    log('Starting data collection')

    # data collection loop
    for sensor in sensors:
        sens = sensor.SENSOR

        # make sure this sensor is already in data_to_save
        if sens not in data_to_save.keys():
                data_to_save[sens] = []
                sensor_indeces[sens] = 0

        index = sensor_indeces[sens]
        sensor_indeces[sens] += 1
        
        try: # in case any sensor fails or is disconnected, the whole system won't crash
            # collect data from sensor
            data = sensor.measure()
            data['sensor'] = sens + str(index) # overwrite sensor info

            # check if there are any diagnostics to report
            if 'diagnostics' in data.keys():
                for diag in data['diagnostics'].keys():
                    if data['diagnostics'][diag]:
                        send_diag = True
                        write_diag('PM' + str(i), diag)

            data_to_save[sens].append(data)
        
        except Exception as e:
            log(f'Error collecting info for {sens}{index}, {sensor.TYPE}')
            write_diag(f'{sens}{index}', str(e))
            send_diag = True
            #raise(e) # for testing right now, exception handling later

    # collect GPS data
    log('collecting GPS data')
    try:
        gps_data = gps.fix()
        data_to_save['date_time_position'] = gps_data
        if(gps_data['latitude'] == None): # GPS has no fix
            raise(Exception('Could not fix GPS'))
    except Exception as e:
        log('Error collecting gps data')
        write_diag('gps', str(e))
        send_diag = True


    # collect date and time for naming files
    curr_time = gps_data['time']
    curr_date = gps_data['date']
    
    # save date-time for diag to use
    try:
        f = open(HOME + 'time.txt', 'w')
    except:
        f = open(HOME + 'time.txt', 'a')

    f.write(curr_time + '\n' + curr_date)
    f.close()

    # collect diagnostics
    log('Collecting diagnostics')
    t, u, _ = disk_usage('/')
    memory = u / t

    temp = CPUTemperature().temperature
    if(temp > 70 or memory > 0.8):
        send_diag = True
        if temp > 70:
            write_diag('temp', str(temp))
        if memory > 0.8:
            write_diag('disk_space', str(memory))
    write_temp_mem(str(temp), str(memory))

    # check to send diagnostics
    if send_diag:
        send_diag = False
        run('sudo systemctl restart diagnostics')

    # file name
    f_name = secure_filename('station' + station_num + '_' + curr_date + 'T' + curr_time + 'Z.json')
    with open(HOME + 'logs/' + f_name, 'w') as f:
        json.dump(data_to_save, f, indent=4)

    # call sender to manage sending of file
    run(f'python3 {HOME}sender.py 10.224.83.51 {HOME}logs/ 0')
    print('sleeping')

    elapsed_time = time.time() - start_measurement_cycle
    time.sleep(max(0, SamplingInterval - elapsed_time)) # protect from possible case where sensor stalls past 10 minutes

    
    
    '''
    PM.powerON()
    data_to_save['particulate_matter_NextPM_0'] = PM.measurePM_1_minute()
    data_to_save['date_time_position'] = onboardGPS.fix()
    if data_to_save['particulate_matter_NextPM_0']['sensor_RH'] < 55.0:
        PM.powerOFF()
    current_date = data_to_save['date_time_position']['date'] 
    current_time = data_to_save['date_time_position']['time']
    logFileName = 'proto0_log_'+current_date+'T'+current_time+'Z.json'
    with open(logFileName, 'w') as logfile:
        json.dump(data_to_save, logfile, indent=4)
    elapsed_time = time.time() - start_measurement_cycle
    time.sleep(SamplingInterval - elapsed_time) 
    '''
