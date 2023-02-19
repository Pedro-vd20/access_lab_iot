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
import datetime
import json
import os
import sensors as sens
from shutil import disk_usage
from gpiozero import CPUTemperature
import station_id as station
import packages.modules as modules
from werkzeug.utils import secure_filename
import threading

#------------------------------------------------
# Constants

SAMPLING_INTERVAL = 600 #in seconds
MAX_SAMPLES = 1

#------------------------------------------------
# Global variables
data_to_save = {}
lock = threading.Lock()
threads = [None] * len(sens.sensors)

#-----------------------------------------------
# functions 

'''
writes an occured error into the diagnostics file located at /home/pi/
@param error_name: error type (air sensor, cpu temperature, exception...)
@param error: string info describing error
appends errors to file until diagnostics sends them
'''
def write_diag(error_name, error):
    with open(os.path.join(modules.HOME, \
        f'station{station.station_num}_diagnostics.txt'), 'a') as f:
        
        # timestamp data
        now = datetime.datetime.now()
        f.write(f'{now.strftime("%Y-%m-%d %H:%M:%S")}\n')

        # clean up error
        error = error.replace('\n', ' ')
        error = error.replace('\r', '')
        error = error.replace('\t', ' ')
        while '  ' in error:
            error = error.replace('  ', ' ')

        f.write(f'{error_name}\n{error}\n\n')

'''
Writes the cpu temperature and disk space in use into the diagnostic file
    the file is located in /home/pi/
'''
def write_temp_mem(temp, mem):
    with open(os.path.join(modules.HOME, \
        f'station{station.station_num}_diagnostics.txt'), 'a') as f:
        
        # timestamp data
        now = datetime.datetime.now()
        f.write(f'{now.strftime("%Y-%m-%d %H:%M:%S")}\n')

        # write error info
        f.write(f'cpu\n{temp}\nmemory\n{mem}\n\n')

'''
Multi-threaded collection of data
Requests data from sensor and checks if sensor provides diagnostics
Manages synchronization for updating global data
Handles exceptions raised by data collection
'''
def measure(sensor, sensor_type, index):
    try: # in case any sensor fails or is disconnected, the whole system won't crash
        # collect data from sensor
        data = sensor.measure()
    except Exception as e: # must catch all exceptions as each sensor may 
                            # raise its own from package library
        modules.log(f'Error collecting info for {sensor_type}{index}, {sensor.TYPE}')
        write_diag(f'{sensor_type}{index}', str(e))
        #raise(e) # for testing right now, exception handling later
        return None # end method, nothing to add to global data_to_save

    # check if there are any diagnostics to report
    if 'diagnostics' in data.keys():
        for diag in data['diagnostics'].keys():
            if data['diagnostics'][diag]:
                write_diag(data['sensor'], diag)
    
    # synchronization for thread writing
    global lock, data_to_save
    lock.acquire()
    data_to_save[sensor_type][index] = data
    lock.release()

    return None

'''
Counts all the sensors connected to the RPi
Creates appropriate list length in data_to_save to allow threads to take charge
'''
def data_init():
    global data_to_save

    for sensor in sens.sensors:
        # get sensor type
        sensor = sensor.SENSOR
        
        # if data_to_save already has a list for this sensor type, add slot 
        #   for new sensor
        if data_to_save.get(sensor, []):
            data_to_save[sensor].append(None)
        else:
            # new list for first sensor of this type
            data_to_save[sensor] = [None]



#-----------------------------------------------

def main():
    while True:
        # collect start time
        start_measurement_cycle = time.time()
        
        global data_to_save
        data_to_save = {} # reset data to save in case it holds data from prev
        modules.log('Starting data collection')

        # count how many of each sensor
        # initialize all lists within data_to_save
        data_init()
        
        # set up data_to_save for data collection
        global threads
        for i, sensor in enumerate(sens.sensors):
            threads[i] = threading.Thread(target=measure, args=(sensor, \
                sensor.SENSOR, sensor.index))

            threads[i].start()

        # collect GPS data while other threads collect sensor data
        modules.log('collecting GPS data')
        try:
            gps_data = sens.gps.fix()
            lock.acquire()
            data_to_save['date_time_position'] = gps_data
            lock.release()
            if(gps_data['latitude'] == None): # GPS has no fix
                raise(Exception('Could not fix GPS'))
        except Exception as e:
            modules.log('Error collecting gps data')
            write_diag('gps', str(e))

        # collect date and time for naming files
        curr_time = gps_data['time']
        curr_date = gps_data['date']
        
        with open(os.path.join(modules.HOME, 'time.txt'), 'w') as f:
            f.write(f'{curr_time}\n{curr_date}')
        
        # collect diagnostics
        modules.log('Collecting diagnostics')
        t, u, _ = disk_usage('/')
        memory = u / t

        temp = CPUTemperature().temperature
        if(temp > 70 or memory > 0.8):
            if temp > 70:
                write_diag('temp', str(temp))
            if memory > 0.8:
                write_diag('disk_space', str(memory))
        write_temp_mem(str(temp), str(memory))

        # join threads
        for thread in threads:
            thread.join()        

        # file name
        f_name = secure_filename(f'station{station.station_num}_{curr_date}T' + \
            f'{curr_time}Z.json')
        with open(os.path.join(modules.HOME, 'data_logs', f_name), 'w') as f:
            json.dump(data_to_save, f, indent=4)

        # call sender to manage sending of file
        os.system(f'python3 {os.path.join(modules.HOME, "sender.py")} ' + \
            f'10.224.83.51 {os.path.join(modules.HOME, "data_logs/")} 0')
        print('sleeping')

        elapsed_time = time.time() - start_measurement_cycle
        time.sleep(max(0, SAMPLING_INTERVAL - elapsed_time)) # protect from possible case where sensor stalls past 10 minutes

    return 0 # should never run


if __name__ == '__main__':
    main()
    
    
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
