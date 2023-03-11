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

import modules.mongo as mongo
from pymongo.errors import ConnectionFailure
import modules.files as files
import os
import json
import sys

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

# constants definitions

MONGO_ADDR = 'localhost'
MONGO_PORT = 27017
DATABASE = 'stations'
GPS = 'date_time_position'

##########


def check_args() -> str:
    '''
    Make sure enough arguments are passed into the script
    Make sure argv[1] is a valid folder
    @return argv[1]
    '''

    # make sure number of arguments
    if len(sys.argv) < 2:
        raise IndexError('Not enough arguments')

    # make sure the provided arg is a valid folder
    if not os.path.isdir(sys.argv[1]):
        raise NotADirectoryError(sys.argv[1])

    return sys.argv[1]


def create_config(dir: str, db: mongo.Mongo) -> None:
    '''
    Goes through the config .json file and extracts the config information to
    add to mongodb
    Assumes ids.json exists in dir
    @param dir path to ids.json
    @param db Mongo object
    '''

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
            'stationary': True,
            'station_num': station_info['station_num']
        }

        # upload to mongo
        db.upload_config(station_num, station)


def upload_files(files_list: list, root: str, db: mongo.Mongo) -> None:
    '''
    Loop through a list of files and upload to mongo
    @param files list of files to read and upload
    @param root root path leading to each file
    '''

    # loop through each of the files
    for f in files_list:
        # skip non-json files
        if f.split('.')[-1] != 'json' or 'diagnostics' in f:
            continue

        # read data from file
        with open(os.path.join(root, f), 'r') as in_f:
            data = json.load(in_f)

        # upload data to mongo
        db.upload_to_mongodb(data,
                             files.get_date(f, True),
                             files.get_station_num(f))


##########


def main():
    # check errors
    folder = check_args()

    # create mongo object to upload data
    mongodb = mongo.Mongo(MONGO_ADDR, MONGO_PORT, DATABASE)

    # test if connection is working
    if not mongodb.test_connection():
        raise ConnectionFailure

    # create config information
    create_config(folder, mongodb)

    # loop through all files
    for root, _, files_list in os.walk(os.path.join(folder, 'received_files')):

        # skip empty dirs
        if not len(files_list):
            continue

        upload_files(sorted(files_list), root, mongodb)

    return 0


if __name__ == '__main__':
    main()
