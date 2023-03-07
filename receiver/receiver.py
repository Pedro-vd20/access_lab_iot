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

"""
From https://flask.palletsprojects.com/en/2.0.x/patterns/fileuploads/
with modifications.

One can upload a file with curl using the command line:

curl -F 'sensor_data_file=@<filename.txt>' -F 'checksum=@<chechsumfilename.sha256>' <web page address>

where: 
<filename> is the name of the file to be uploaded.
<chechsumfilename> is the name of the textfile produced by running sha256sum 
                   in binary mode on <filename.txt> 
                   (e.g.: sha256sum -b pippo.txt > pippo.sha256).
<web page address> is the url of the upload page, e.g. http://127.0.0.1:5000/
"""

import os
import hashlib
import datetime
from flask import Flask, request
from werkzeug.utils import secure_filename
from random import choice
from string import ascii_letters
import json
import pymongo # for safety and consistency, we should change to Flask-PyMongo 

client = pymongo.MongoClient("mongodb://localhost:<port>/")
stations_db = client["stations"]

# only accept txt and sha256 files
ALLOWED_EXTENSIONS = {'txt', 'json', 'csv'}
# place to permanently store files
STORAGE_FOLDER = '/home/pv850/received_files/'
DIAGNOSTICS = '/home/pv850/diagnostics/'
# place where all pi ids are stored
PI_ID_F = 'ids.json'
# how long urls will be
URL_LEN = 20

#---------------------------------------------------------

def log(msg):
    # get current time
    now = datetime.datetime.now() 
    year = now.year
    month = now.month

    # change to db
    with open(f'logs/{year}_{month}.txt', 'a') as f:
        f.write(now.strftime('[%Y-%m-%d %H:%M:%S] '))
        f.write(f'{msg}\n')


# check file extension for validity
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# check the checksum of a file
def verify_checksum(fname, chksm):
    # check file validity
    if not os.path.isfile(fname):
        return False
    
    with open(fname, 'rb') as f:
        hash_256 = hashlib.sha256(f.read()).hexdigest()
    
    return hash_256 == chksm


# verify a pi's id
def is_auth(pi_id):
    # check for empty arg
    if pi_id == '':
        return False

    # load ids
    # change to use db
    with open(PI_ID_F, 'r') as ids:
        data = json.load(ids)
    

    auth = data.get(pi_id, None)
    return auth != None
    

# generate random string
def gen_rand_string():
    return ''.join([choice(ascii_letters) for i in range(URL_LEN)])

# add an email to a station
def register_email(auth, email):
    # load data
    with open(PI_ID_F, 'r') as ids:
        data = json.load(ids)

    # add email
    data[auth]['email'] = email
    # get station num
    num = data[auth]['station_num']

    # save info
    with open(PI_ID_F, 'w') as ids:
        json.dump(data, ids, indent=4)

    # create folder for this station
    os.system(f'mkdir {STORAGE_FOLDER}station{num}')
    os.system(f'mkdir {DIAGNOSTICS}station{num}')

    return f'{STORAGE_FOLDER}station{num}'
    

'''
Collect the date from a given filename
Files are written station<num>_<year>-<month>-<day>T<hour>Z.json
'''
def get_date(file_str):
    date = file_str.split('_')[1].split('-')
    year = date[0]
    month = date[1]

    return f'{year}_{month}'

def get_month_from_datetime(date: str): #CHANGE THIS TO USE FILENAME
    if date == None: 
        return ""
    return "{}_{}".format(date[5:7],date[0:4])

def read_json(raw_json): 
        gps = raw_json["date_time_position"]
        particulate_matter = raw_json["particulate_matter"]
        air_sensor = raw_json["air_sensor"]
        sensor_types = [gps, particulate_matter, air_sensor] # it might make more sense to make this a dict.

        # for extra in raw_json:
        #     if extra != "particulate matter" and extra != "air_sensor" and extra != "date_time_position":
        #         sensor_types.append(raw_json[extra])

        return sensor_types


def upload_to_mongodb(raw_json, station_num):
    sensor_types = read_json(raw_json) 
    month = get_month_from_datetime(sensor_types[0]["date"])
    
    station_col = stations_db["station"+station_num]
    station_col.update_one({"month": month}, # specific template for consistency and testing/debugging, will be changed to for loop
                           {"$push" : {"particulate_matter.PM1count.0" : raw_json["particulate_matter"][0]["PM1count"],
                                    "particulate_matter.PM1count.1" : raw_json["particulate_matter"][1]["PM1count"],
                                    "particulate_matter.PM2,5count.0" : raw_json["particulate_matter"][0]["PM2.5count"],
                                    "particulate_matter.PM2,5count.1" : raw_json["particulate_matter"][1]["PM2.5count"],
                                    "particulate_matter.PM10count.0" : raw_json["particulate_matter"][0]["PM10count"],
                                    "particulate_matter.PM10count.1" : raw_json["particulate_matter"][1]["PM10count"],
                                    "particulate_matter.PM1mass.0" : raw_json["particulate_matter"][0]["PM1mass"],
                                    "particulate_matter.PM1mass.1" : raw_json["particulate_matter"][1]["PM1mass"],
                                    "particulate_matter.PM2,5mass.0" : raw_json["particulate_matter"][0]["PM2.5mass"],
                                    "particulate_matter.PM2,5mass.1" : raw_json["particulate_matter"][1]["PM2.5mass"],
                                    "particulate_matter.PM10mass.0" : raw_json["particulate_matter"][0]["PM10mass"],
                                    "particulate_matter.PM10mass.1" : raw_json["particulate_matter"][1]["PM10mass"],
                                    "particulate_matter.sensor_T.0" : raw_json["particulate_matter"][0]["sensor_T"],
                                    "particulate_matter.sensor_T.1" : raw_json["particulate_matter"][1]["sensor_T"],
                                    "particulate_matter.sensor_RH.0" : raw_json["particulate_matter"][0]["sensor_RH"],
                                    "particulate_matter.sensor_RH.1" : raw_json["particulate_matter"][1]["sensor_RH"],
                                    "air_sensor.humidity.0" : raw_json["air_sensor"][0]["humidity"],
                                    "air_sensor.humidity.1" : raw_json["air_sensor"][1]["humidity"],
                                    "air_sensor.temperature.0" : raw_json["air_sensor"][0]["temperature"],
                                    "air_sensor.temperature.1" : raw_json["air_sensor"][1]["temperature"],
                                    "air_sensor.pressure.0" : raw_json["air_sensor"][0]["pressure"],
                                    "air_sensor.pressure.1" : raw_json["air_sensor"][1]["pressure"],
                                    "gps.datetime" : (raw_json["date_time_position"]["date"] + "T" + raw_json["date_time_position"]["time"] + "Z"),
                                    "gps.date" : raw_json["date_time_position"]["date"],
                                    "gps.time" : raw_json["date_time_position"]["time"],
                                    "gps.latitude" : raw_json["date_time_position"]["latitude"],
                                    "gps.lat_dir" : raw_json["date_time_position"]["lat_dir"],
                                    "gps.longitude" : raw_json["date_time_position"]["longitude"],
                                    "gps.lon_dir" : raw_json["date_time_position"]["lon_dir"],
                                    "gps.altitude" : raw_json["date_time_position"]["altitude"],
                                    "gps.alt_unit" : raw_json["date_time_position"]["alt_unit"],
                                    "gps.num_sats" : raw_json["date_time_position"]["num_sats"],
                                    "gps.PDOP" : raw_json["date_time_position"]["PDOP"],
                                    "gps.HDOP" : raw_json["date_time_position"]["HDOP"],
                                    "gps.VDOP" : raw_json["date_time_position"]["VDOP"]
                                    },
                                    "$set" : {"particulate_matter.type.0" : raw_json["particulate_matter"][0]["type"],
                                          "particulate_matter.type.1" : raw_json["particulate_matter"][1]["type"],
                                          "air_sensor.type.0": raw_json["air_sensor"][0]["type"],
                                          "air_sensor.type.1" : raw_json["air_sensor"][1]["type"]}})
    
    return ""

#---------------------------------------------------------

# make sure the necessary paths are available
if not (os.path.isfile(PI_ID_F) and \
  os.path.isdir(STORAGE_FOLDER) and \
  os.path.isdir(DIAGNOSTICS)):
    log('Error finding files and folders')
    raise(FileNotFoundError('Missing files and folders'))


# dictionary to keep mapping of random urls to pi ids
urls = {}

app = Flask(__name__)
app.config['SECRET_KEY'] = '1234567'
app.config['MAX_CONTENT_LENGTH'] = 1024 * 128 # max file size (in KB)
app.config['STORAGE_FOLDER'] = STORAGE_FOLDER

log('Server running')

#---------------------------------------------------------

# page for users to request their access station
@app.route('/', methods=['GET'])
def home():
    return 'Temporarily out of order'

# page to display access station data
@app.route('/view/<station>')
def view_station(station):
    return 'Temporarily out of order'

# page to register new access station to system
# adds user email to database so they can check their station
@app.route('/register/', methods=['POST'])
def register():
    # collect headers
    auth = request.headers.get('pi_id', None)
    email = request.headers.get('email', None)

    # if id doesn't match
    if (auth == None) or (not is_auth(auth)):
        log('Unauthorized access, rejected')
        return '401'

    # Missing data
    if email == None or 'sensor_config' not in request.files or \
        'checksum' not in request.headers:
        
        log('Required data not in request')    
        return '412'

    # add email to db
    station_dir = register_email(auth, email)

    log('Email registered')

    # save config file
    datafile = request.files['sensor_config']
    checksum = request.headers['checksum']

    # check for empty fields / None
    if ((datafile.filename == '') or (checksum == '')):
        log('Empty file or checksum fields')
        return '412'

    # check for allowed file extensions
    if (not allowed_file(datafile.filename)):
        log('Unsupported file type')
        return '415'

    # save data and validate checksum
    # add to DB
    datafile.save(f'{station_dir}sensors_config.txt')
    if not verify_checksum(f'{station_dir}sensors_config.txt', checksum):
        # remove file
        os.system(f'rm {station_dir}sensors_config.txt')
        log('Sensor config file could not be verified')
        return '500'

    return '200'
        

# authentication route
# verifies id sent by pi 
# if authenticated, returns route to upload files
@app.route('/upload/', methods=['GET'])
def authenticate():
    # collect headers from request
    auth = request.headers.get('pi_id', None)

    # if request has no authentication or wrong id
    if ((auth == None) or (not is_auth(auth))):
        log('Unathorized access, rejected')
        return '401'

    # generate random url for data transfer
    url = gen_rand_string()
    # make sure rand url isn't in use
    global urls
    while urls.get(url, None) != None:
        url = gen_rand_string()

    log(f'New request from {auth}, opening /upload/{url}')

    # store mapping of id to random url
    urls[url] = auth      
    
    return '301 ' + url


# data transfer route
# verifies again that sender has a verified id and is 
    # transmitting to the correct channel
@app.route('/upload/<url>', methods=['POST'])
def get_file(url):
    # collect headers for authentication
    auth = request.headers.get('pi_id', None)

    # verify if authorized 
    if ((auth == None) or (urls.get(url, None) == None) or (urls[url] != auth)):
        log('Unauthorized request, rejected')
        return '401'

    # check how many remaining files
    #   all arguments are in string form
    num_files = request.headers.get('num_files', '1')
    if(num_files == '1'):
        # remove url - pi pair from existing urls
        urls.pop(url)

    # receive files
    # check if post request has the files
    if (('sensor_data_file' not in request.files) or 
            ('checksum' not in request.headers) or ('pi_num' not in request.headers)):
        log('Required data not in request')
        return '412'

    # collect files
    raw_json = request.get_json()
    datafile = request.files['sensor_data_file']
    checksum = request.headers['checksum']
    station_num = request.headers['pi_num']
    
    # check for empty fields / None
    if ((datafile.filename == '') or (checksum == '')):
        log('Empty file or checksum fields')
        return '412'

    # check for allowed file extensions
    if (not allowed_file(datafile.filename)):
        log('Unsupported file type')
        return '415'
    
    # create local names for files
    if 'diagnostic' in datafile.filename:
        storage_folder = f'{DIAGNOSTICS}station{station_num}/'
    else:
        storage_folder = f'{STORAGE_FOLDER}station{station_num}/' + \
            f'{get_date(datafile.filename)}/'
        # Check if this folder exists, if not create
        if not os.path.isdir(storage_folder):
            os.mkdir(storage_folder)
        
    data_f_name = os.path.join(storage_folder, secure_filename(datafile.filename))
    data_f_name_temp = os.path.join(storage_folder, secure_filename('temp_' + datafile.filename))

    name = datafile.filename.split('.')[0]
    checksum_f_name = os.path.join(storage_folder, 
            secure_filename(name + '.sha256'))

    # save data file
    datafile.save(data_f_name_temp)
    
    upload_to_mongodb(raw_json, station_num)

    # verify checksum
    chksm = verify_checksum(data_f_name_temp, checksum)
    if chksm: # successful verification
        log(f'Checksum verified successfully, storing {data_f_name}')
        
        # save checksume file
        with open(checksum_f_name, 'w') as f:
            f.write(f'{checksum} {secure_filename(datafile.filename)}\n')

        # remove temp file
        os.system(f'mv {data_f_name_temp} {data_f_name}')

        # return success code
        return '200'

    else:
        print('Wrong checksum')
        # delete store file
        os.remove(data_f_name_temp)

        # return error
        return '500'
    