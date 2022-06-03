import time
import json
import os
import random
from datetime import datetime, timezone
from secret import secret
from sender import main as mn


SAMPLING_INTERVAL = 600 # seconds
MAX_SAMPLES = 100

def main():
    count = 0

    while count < MAX_SAMPLES:
        start_time = time.time()
        count += 1
        
        date = datetime.now(timezone.utc).isoformat()
        
        if '.' in date:
            index = date.index('.')
            date = date[:index]

        date += 'Z'
        
        try:
            f = open('logs/' + date + '.json', 'w')
        except:
            f = open('logs/' + date + '.json', 'a')

        f.write('{\n\t"particulate_matter_NextPM_0": {\n')

        pm1 = random.randint(200, 500)
        f.write('\t\t"PM1count": ' + str(pm1) + ',\n')
        pm2 = random.randint(300, 600)
        f.write('\t\t"PM2.5count": ' + str(pm2) + ',\n') 
        pm10 = random.randint(250, 550)
        f.write('\t\t"PM10count:": ' + str(pm10) + ',\n')
        mass1 = random.random() * 100
        f.write('\t\t"PM1mass": ' + str(mass1) + ',\n')
        mass2_5 = random.random() * 100
        f.write('\t\t"PM2.5mass": ' + str(mass2_5) + ',\n')
        mass10 = random.random() * 150 + 50
        f.write('\t\t"PM10mass": ' + str(mass10) + ',\n')
        sensor_t = random.random() * 100
        f.write('\t\t"sensor_T": ' + str(sensor_t) + ',\n')
        sensor_rh = random.random() * 100
        f.write('\t\t"sensor_RH": ' + str(sensor_rh) + ',\n')

        f.write('\t\t"Degraded": false,\n\t\t"Notread": false,\n\t\t"Eccess_RH": false,\n\t\t"T_RH_off": false,\n\t\t"Fan_error": false,\n\t\t"Mem_error": false,\n\t\t"Lass_error": false\n\t},\n')

        f.write('\t"date_time_position": {\n')

        dt = date[:10]
        f.write('\t\t"date": "' + dt + '",\n')
        tm = date[11:19]
        f.write('\t\t"time": "' + tm + '",\n')

        f.write('\t\t"latitude": 24.52,\n\t\t"lat_dir": "N",\n\t\t"longitude": 54.43,\n\t\t"lon_dir": "E",\n\t\t"altitude": 76.2,\n\t\t"alt_unit": "M",\n\t\t"num_stats": 7,\n\t\t"PDOP": 3.54,\n\t\t"HDOP": 3.15,\n\t\t"VDOP": 1.62\n\t}\n}')

        f.close()

        # os.sys('python3 sender.py 10.224.83.51 logs/')
        mn(['sender.py', '10.224.83.51', 'logs/'])
        elapsed_time = time.time() - start_time
        time.sleep(SAMPLING_INTERVAL - elapsed_time)

    return 0

if __name__ == '__main__':
    main()
