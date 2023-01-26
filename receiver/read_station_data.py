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

#from pylab import *
import json
import os
from datetime import datetime
from dateutil.parser import parse as timestring_to_datetime
import numpy as np
import pandas as pd

# collect data in numpy format
def collect_data(station_num):
    path = os.path.join('/home/pv850/received_files/station', str(station_num))
    if not os.path.isdir(path):
        raise(FileNotFoundError(f'{path} not found'))
    
    files = os.listdir(path)

    # remove checksum files
    files = [f if 'sha256' not in f else None for f in files]
    while None in files:
        files.remove(None)

    files.sort()

    # find out how many files left
    num_files = len(files)
    
    # find out number of sensors for each
    with open(os.path.join(path, files[0]), 'r') as f_read:
        data = json.load(f_read)
    num_pm = len(data['particulate_matter'])
    num_air_sens = len(data['air_sensor'])
    
    ##########
    # initialize all data
    pm = {'PM1count': np.zeros((num_pm, num_files), dtype=float),
          'PM1mass': np.zeros((num_pm, num_files), dtype=float),
          'PM2.5count': np.zeros((num_pm, num_files), dtype=float),
          'PM2.5mass': np.zeros((num_pm, num_files), dtype=float),
          'PM10count': np.zeros((num_pm, num_files), dtype=float),
          'PM10mass': np.zeros((num_pm, num_files), dtype=float),
          # the following only appear in either the sps30 or NEXTPM, but not both, so must 
          # check if key is present
          'sensor_T': np.zeros((num_pm, num_files), dtype=float),
          'sensor_RH': np.zeros((num_pm, num_files), dtype=float),
          'PM4count': np.zeros((num_pm, num_files), dtype=float),
          'PM4mass': np.zeros((num_pm, num_files), dtype=float),
          'PM0.5count': np.zeros((num_pm, num_files), dtype=float),
          'PM0.5mass': np.zeros((num_pm, num_files), dtype=float),
          'Typical_particle_size': np.zeros((num_pm, num_files), dtype=float)
         }
    air_sens = {'humidity': np.zeros((num_air_sens, num_files), float),
                'temperature': np.zeros((num_air_sens, num_files), float),
                'pressure': np.zeros((num_air_sens, num_files), float)
               }

    gps = {'time': np.zeros(num_files, dtype=datetime),
           'latitude': np.zeros(num_files, dtype=float), 
           'lat_dir': np.empty(num_files, dtype=str),
           'longitude': np.zeros(num_files, dtype=float),
           'lon_dir': np.empty(num_files, dtype=str),
           'altitude': np.zeros(num_files, dtype=float),
           'alt_unit': np.empty(num_files, dtype=str),
           'num_sats': np.zeros(num_files, dtype=float),
           'PDOP': np.zeros(num_files, dtype=float),
           'HDOP': np.zeros(num_files, dtype=float),
           'VDOP': np.zeros(num_files, dtype=float)
          }
    
    
    # loop through files collecting data
    for i in range(len(files)):
        # collect json data
        with open(os.path.join(path, files[i]), 'r') as f_read:
            data = json.load(f_read)

        # add pm
        for sens in data['particulate_matter']:
            index = int(sens['sensor'][-1]) # collect the index
            # the assumption here is that no box will have more than 10 sensors
            
            for key in sens.keys():
                if key in ('diagnostics', 'sensor'):
                    continue
                pm[key][index][i] = sens[key]
 
        # add air sensor info
        for sens in data['air_sensor']:
            index = int(sens['sensor'][-1])

            for key in sens.keys():
                if key in ('type', 'sensor'):
                    continue
                air_sens[key][index][i] = sens[key]

        # add gps info
        for key in data['date_time_position'].keys():
            if key in ('date', 'time'):
                continue
            temp = data['date_time_position'][key]
            if temp == None:
                gps[key][i] = np.nan
            else:
                gps[key][i] = temp
        # add date time
        gps['time'][i] = timestring_to_datetime(data['date_time_position']['date'] \
                + 'T' + data['date_time_position']['time'] + 'Z')

    return pm, air_sens, gps


'''
From:
old_dict:   {
                property: [ [sensor0_measure0, sensor0_measure1...],
                            [sensor1_measure0, sensor1_measure1...],
                            ...
                          ]
            }
to:
new_dict:   {
                property_sensor0: [measure0, measure1,...],
                property_sensor1: [measure0, measure1,...]
'''
def __unify_dict(new_dict, old_dict, sensor, num_sensors):
    for key in old_dict.keys():
        new_key = sensor + '_' + key
        if num_sensors > 1:
            for i in range(num_sensors):
                new_dict[new_key + '_' + str(i)] = old_dict[key][i]
        else:
            new_dict[new_key] = old_dict[key]

# collect data in pandas format
def collect_data_pd(station_num):
    pm, air_sens, gps = collect_data(station_num)
    
    # prepare dictionary for pandas
    main_dict = {}
    
    # find how many sensors
    num_pm = pm['PM1count'].shape[0] # both 'PM1count' and 'temperature' are 
    num_air = air_sens['temperature'].shape[0] # measures present in all sensor types,
                                        # regardless of manufacturer

    __unify_dict(main_dict, pm, 'pm', num_pm)
    __unify_dict(main_dict, air_sens, 'air_sensor', num_air)
    __unify_dict(main_dict, gps, 'gps', 1)

    return pd.DataFrame(main_dict)


