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

'''
This file will go through a list of existing data files that have NEVER been 
uploaded to the mongo server and will upload them all in order

receiver.py should have the task of regularly updating to mongo, this script 
is for single use to migrate the old files to the new Mongo implementation

Expected folder structure:
./received_files/
 |- station0/
 |   |- 07_22/
 |   |   |- station0_2022-07-15T000043Z.json
 |   |   ...
 |   |- 08_22/
 |   ...
 |- station1/
 ...
 |- stationn/
'''

##########

import pymongo
import sys
import os
import json
import datetime

##########

MONGO_ADDR = 'localhost'
MONGO_PORT = 27017
DATABASE = 'test-2'
GPS = 'date_time_position'

##########

'''
Uses sys.argv to extract the arguments
Checks if folder exists, assumes correct folder structure 
Expects the following folder structure:
    ./
        received_files/
            station0/
                09_22/
                    data_files.json
                    data_files.sha256
                    ...
                ...
            ...
        ids.json
'''
def check_folder():
    # check if arg present
    if len(sys.argv) < 2:
        raise(IndexError('Not enough arguments'))

    # check if folder exists
    if not os.path.isdir(sys.argv[1]):
        raise(FileNotFoundError(f'{sys.argv[1]} is not a directory'))
    
    return sys.argv[1]


'''
Goes through the config .json file and extracts the config information to add
to mongodb
Assumes ids.json exists in dir
@param dir path to ids.json
@param db MongoDB database object
'''
def create_config(dir, db):
    # collect all info from ids.json
    with open(os.path.join(dir, 'ids.json'), 'r') as in_f:
        config_data = json.load(in_f)

    # loop through each station collecting the relevant config data only
    for station_id, station_info in config_data.items():
        # collect station num
        station_num = f'station{station_info["station_num"]}'
    
        # create config dictionary
        station = {
            'config': True,
            'sensors': station_info['sensors'],
            'id': station_id,
            'email': station_info['email'],
            'stationary': True
        }

        # upload to mongo
        db[station_num].insert_one(station)


'''
Filters a list of file names for only .json files
@param dir path to files
@return sorted list of all .json files in dir
'''
def filter_data(dir):
    data_files = []

    '''
    Walk through the file structure in search for data files
    ./root_folder/
        ./month_folder/
            data_files
            ...
        ./month_folder/
            data_files
            ...
    '''
    for root, _, files in os.walk(dir):
        # skip non-leave directories
        if not len(files):
            continue
            
        # filter out non-json files, then add the full path to them, and then 
        # append them to data_files
        data_files += [os.path.join(root, f) for f in \
                       filter(lambda f_name: '.json' in f_name, files)]

    return sorted(data_files)
    

'''
loops through a file and uploads it to mongo
@param f_name name of file to open
@param station_collection mongodb collection object to upload data into
'''
def upload_data(f_name, station_collection):
    # collect data date from f_name
    date = get_date(f_name)

    # collect data
    with open(f_name, 'r') as in_f:
        data = json.load(in_f)

    # check if month exists in the database
    if station_collection.find_one({'month': date}) is None:
        # if none, create template for the data
        station_collection.insert_one(create_template(data, date))

    # fill in station info for each sensor type
    for sensor in data:
        if sensor == GPS:
            # fill in gps info
            add_gps(data[GPS], date, station_collection)
            continue

        add_sensor(sensor, data[sensor], date, station_collection)

    

'''
Gets the month and year from a file name string
@param f_name string with file name
File name shoud be station<n>_YYYY-MM-DDT...Z.json
@return string MM_YYYY
'''
def get_date(f_name):
    date = f_name.split('/')[-1].split('_')[1].split('-')

    year = date[0]
    month = date[1]

    return f'{month}-{year}'


'''
Creates an empty template for the data to be added
@param data file with data to create template
@return dictionary template for data
'''
def create_template(data, month):
    template = {'month': month}

    for sensor in data:
        
        # special treatment of gps
        if sensor == GPS:
            template['gps'] = {
                'datetime': [], 
                'position': [],
                'altitude': [],
                'altitude_unit': 'M'
                }
            continue

        # collect num sensors
        sens_num = len(data[sensor])
        template[sensor] = {}

        # go through all the sensor measurements
        for measurement in data[sensor][0]:
            # skip sensor
            if measurement == 'sensor':
                continue
            # type needs not be 
            elif measurement == 'type':
                template[sensor][measurement] = {str(i): data[sensor][i][measurement] for i in range(sens_num)}
                continue



            measurement = measurement.replace('.', ',') # replace . with , as 
                                                # it would create mongo issues
            template[sensor][measurement] = {str(i): [] for i in range(sens_num)}

    return template


'''
Creates a datetime object out of the collected info
Creates a position object out of the collected info
Uploads the data to the mongo_collection
'''
def add_gps(gps_data, date, mongo_collection):
    date_string = f'{gps_data["date"]}T{gps_data["time"]}Z'
    # print(date_string)
    

    mongo_collection.update_one({'month': date}, {
        '$push': {
            'gps.datetime': datetime.datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%SZ'),
            'gps.altitude': gps_data['altitude'],
            'gps.position': [gps_data['longitude'], gps_data['latitude']]
        }
    })



'''
Loops through sensor list and adds all data to respective index
Uploads the data to the mongo_collection
'''
def add_sensor(sensor, sensor_list, month, mongo_collection):
    # loop through each sensor
    for i, data in enumerate(sensor_list):
        # remove non-necessary keys
        data.pop('sensor')
        data.pop('type')
        
        # push to mongodb
        mongo_collection.update_one({'month': month}, {
            '$push': {f'{sensor}.{key.replace(".", ",")}.{i}': value for key, value in data.items()}
        })
    




##########

def main():
    # Check valid folder structure
    src_folder = check_folder() # will raise exception if no folder exists
    stations_folder = os.path.join(src_folder, 'received_files')

    # check mongodb connection
    client = pymongo.MongoClient(MONGO_ADDR, MONGO_PORT)
    try:
        client.server_info()
    except pymongo.errors.ServerSelectionTimeoutError:
        print(f'Failed to connect to the database at {MONGO_ADDR}/{MONGO_PORT}')
        return -1
    db = client[DATABASE]

    # Looping through all files assumes folder structure is the same as listed 
    # above and all files are valid
    stations = os.listdir(stations_folder)
    create_config(src_folder, db)

    for station in stations:

        # get all the files in the station directory
        folder_path = os.path.join(stations_folder, station)
        data_files = filter_data(folder_path)
                        # collect sorted list of .json files ONLY, ignore .sha256  

        for data_f in data_files: 
            upload_data(data_f, db[station])

    return 0

if __name__ == '__main__':
    main()