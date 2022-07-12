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

    f_line = f.readline()

    if f_line == '':
        log('No diagnostics to send')
        time.sleep(600)
        continue

    f.close()
    
    # get time
    try:
        f = open(HOME + 'time.txt', 'r')
    except:
        time.sleep(600) # wait for first round of data collection
        continue
    curr_time = f.readline().strip()
    curr_date = f.readline().strip()

    f_name = secure_filename('station' + station_num + '_' + curr_date + 'T' + curr_time + 'Z_diagnostics.json')

    run('mv ' + diag_file + ' ' + HOME + 'logs/' + f_name)
    run('touch ' + diag_file)

    elapsed = time.time() - start_measurement_cycle
    time.sleep(SamplingInterval - elapsed)


if __name__ == '__main__':
    main()
