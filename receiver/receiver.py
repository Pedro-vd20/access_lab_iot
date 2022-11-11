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
from flask import Flask, flash, request, redirect, url_for
from numpy import void
from werkzeug.utils import secure_filename
from random import choice
from string import ascii_letters
import json

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

    with open('logs/{year}_{month}_logs.txt', 'a') as f:
        f.write(now.strftime('[%Y-%m-%d %H:%M:%S] '))
        f.write(msg + '\n')


# check file extension for validity
def allowed_file(filename: str) -> bool:
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# check the checksum of a file
def verify_checksum(fname: str, chksm: str) -> bool:
    with open(fname, 'rb') as f:
        hash_256 = hashlib.sha256(f.read()).hexdigest()
    
    return hash_256 == chksm


# verify a pi's id
def is_auth(pi_id: str) -> bool:

    if pi_id == '':
        return False

    # load ids
    ids = open(PI_ID_F, 'r')
    data = json.load(ids)
    ids.close()

    auth = data.get(pi_id, None)
    return auth != None
    

# generate random string
def gen_rand_string() -> str:
    return ''.join([choice(ascii_letters) for i in range(URL_LEN)])

# add an email to a station
def register_email(auth, email):
    # load data
    ids = open(PI_ID_F, 'r')
    data = json.load(ids)
    ids.close()

    # add email
    data[auth]['email'] = email
    # get station num
    num = data[auth]['station_num']

    ids = open(PI_ID_F, 'w')
    json.dump(data, ids, indent=4)
    ids.close()

    # create folder for this station
    os.system('mkdir ' + STORAGE_FOLDER + 'station' + str(num))
    os.system('mkdir ' + DIAGNOSTICS + 'station' + str(num))
    

#---------------------------------------------------------

# make sure the necessary paths are available
try:
    f = open(PI_ID_F, 'r')
    f.close()
    os.listdir(STORAGE_FOLDER)
    os.listdir(DIAGNOSTICS)
except:
    log('Error finding files and folders')
    exit(-1)

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

    if email == None:
        log('Required data not in request')    
        return '412'

    # add email to database
    register_email(auth, email)
    log('Email registered')

    return '200'
        

# authentication route
# verifies id sent by pi
# if authenticated, returns route to upload files
@app.route('/upload/', methods=['GET'])
def authenticate():
    # collect headers from request
    auth = request.headers.get('pi_id', None)
    num_files = request.headers.get('num_files', None)

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

    log('New request from ' + auth + ', opening ' + '/upload/' + url)

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
        storage_folder = DIAGNOSTICS + 'station' + station_num + '/'
    else:
        storage_folder = app.config['STORAGE_FOLDER'] + 'station' + station_num + '/'
    data_f_name = os.path.join(storage_folder, secure_filename(datafile.filename))
    data_f_name_temp = os.path.join(storage_folder, secure_filename('temp_' + datafile.filename))

    name = datafile.filename.split('.')[0]
    checksum_f_name = os.path.join(storage_folder, 
            secure_filename(name + '.sha256'))

    # save data file
    datafile.save(data_f_name_temp)
    
    # verify checksum
    chksm = verify_checksum(data_f_name_temp, checksum)
    if chksm: # successful verification
        log('Checksum verified successfully, storing ' + data_f_name)
        
        # save checksume file
        try:
            f = open(checksum_f_name, 'w')  # overwrites if file already exists
        except:
            f = open(checksum_f_name, 'a')  # creates file if doesn't exist
        f.write(checksum)
        f.write(' ' + secure_filename(datafile.filename) + '\n')
        f.close()

        # remove temp file
        os.system('mv ' + data_f_name_temp + ' ' + data_f_name)

        # return success code
        return '200'

    else:
        print('Wrong checksum')
        # delete store file
        os.remove(data_f_name_temp)

        # return error
        return '500'
