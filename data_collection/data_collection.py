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

def write_diag(error):
    f = open(HOME + 'station' + station_num + '_diagnostics.txt', 'a')
    
    now = datetime.datetime.now()
    f.write(now.strftime('%Y-%m-%d %H:%M:%S,'))
    
    error = error.replace('\n', ' ')
    error = error.replace('\r', '')
    error = error.replace('\t', ' ')

    while '  ' in error:
        error = error.replace('  ', ' ')

    f.write(error)
    f.write('\n')
    f.close()

#-----------------------------------------------
nerror = 0

send_diag = False
PM_DIAG = ('Degraded', 'Notready', 'Eccess_RH', 'T_RH_off', 'Fan_error', 'Mem_error', 'Las_error')

while True:
    start_measurement_cycle = time.time()
    data_to_save = {}

    log('Collecting data')

    print('Collecting NEXTPM data')
    # collect PM data
    for i in range(len(pm)):
        print(i)
        try:
            print('Turning on')
            pm[i].powerON()
            print('collecting data')
            data = pm[i].measurePM_1_minute()
            print('checking humidity')
            if data['sensor_RH'] < 55.0:
                pm[i].powerOFF()
            print('saving data')
            data_to_save['particulate_matter_NextPM_' + str(i)] = data
            
            # check diagnostics on PM
            print('checking diagnostics')
            for diag in PM_DIAG:
                if data[diag]:
                    send_diag = True
                    write_diag('PM' + str(i) + ',' + diag)
            
        except Exception as e:
            log('Error collecting info for PM ' + str(i))
            write_diag('PM' + str(i) + ',' + str(e)) 
            send_diag = True
            
    print('Collecting air sensor data')
    # collect air data
    for i in range(len(air_sens)):
        try:
            data = air_sens[i].measureATM()
            data_to_save['air_sensor' + str(i)] = data
        except Exception as e:
            log('Error collecting info for air sensor' + str(i))
            write_diag('air_sensor' + str(i) + ',' + str(e))
            send_diag = True
    
    print('collecting GPS data')
    # collect GPS data
    try:
        gps_data = gps.fix()
        data_to_save['date_time_position'] = gps_data
        if(gps_data['latitude'] == None):
            raise(Exception('Could not fix GPS'))
    except Exception as e:
        log('Error collecting gps data')
        write_diag('gps,' + str(e))
        send_diag = True

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
    print('Collecting diagnostics')
    t, u, _ = disk_usage('/')
    memory = u / t
    write_diag('memory,' + str(memory))
    if(memory > 0.8):
        send_diag = True

    temp = CPUTemperature().temperature
    write_diag('temperature,' + str(temp))
    if(temp > 70):
        send_diag = True


    # check to send diagnostics
    if send_diag:
        send_diag = False
        run('sudo systemctl restart diagnostics')

    # file name
    f_name = secure_filename('station' + station_num + '_' + curr_date + 'T' + curr_time + 'Z.json')
    with open(HOME + 'logs/' + f_name, 'w') as f:
        json.dump(data_to_save, f, indent=4)
    
    # send
    run('python3 ' + HOME + 'sender.py 10.224.83.51 ' + HOME + 'logs/ 0')

    print('sleeping')
    elapsed_time = time.time() - start_measurement_cycle
    time.sleep(SamplingInterval - elapsed_time)

    
    
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
