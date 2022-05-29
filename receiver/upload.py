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
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename
from random import choice
from string import ascii_letters

# only accept txt and sha256 files
ALLOWED_EXTENSIONS = {'txt', 'json', 'csv'}
# place to permanently store files
STORAGE_FOLDER = '/home/pi/received_files/'
# place where all pi ids are stored
PI_ID_F = '/home/pi/receiver/ids.txt'
# how long urls will be
URL_LEN = 20

# dictionary to keep mapping of random urls to pi ids
urls = {}

app = Flask(__name__)
app.config['SECRET_KEY'] = '1234567'
app.config['MAX_CONTENT_LENGTH'] = 1024 * 128 # max file size (in KB)
app.config['STORAGE_FOLDER'] = STORAGE_FOLDER

#---------------------------------------------------------

# check file extension for validity
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# check the checksum of a file
def verify_checksum(fname, chksm):
    with open(fname, 'rb') as f:
        hash_256 = hashlib.sha256(f.read()).hexdigest()
    
    return hash_256 == chksm

# verify a pi's id
def is_auth(pi_id):
    ids = open(PI_ID_F, 'r')
    
    ids = [line.strip() for line in ids]

    return (pi_id != '') and (pi_id in ids)

# generate random string
def gen_rand_string():
    return ''.join([choice(ascii_letters) for i in range(URL_LEN)])
    

#---------------------------------------------------------

# authentication route
# verifies id sent by pi
# if authenticated, returns route to upload files
@app.route('/', methods=['GET'])
def authenticate():
    # collect headers from request
    auth = request.headers.get('pi_id', None)
    num_files = request.headers.get('num_files', None)

    print('New request in, auth =', auth)

    # if request has no authentication or wrong id
    if ((auth == None) or (not is_auth(auth))):
        print('unathorized access, rejected')
        return ''
        # check internal flask functionality for returning standard errors

    # check num_files
    if (num_files == None or type(num_files) != type(1)):
        num_files = 1

    # generate random url for data transfer
    url = gen_rand_string()
    # MAKE SURE THIS RAND URL ISNT OCCUPIED

    print('New random url:', url)

    # store mapping of id to random url
    urls[url] = [auth, num_files] # MAKE THIS A TUPLE (AUTH, NUM_FILES_TO_SEND)
    # TESTING THIS PART IS IMPORTANT

    print('Success')
    
    return url


# data transfer route
# verifies again that sender has a verified id and is 
    # transmitting to the correct channel
@app.route('/upload/<url>', methods=['POST'])
def get_file(url):
    # collect headers for authentication
    auth = request.headers.get('pi_id', None)

    print('New request in, auth =', auth)

    # verify if authorized 
    if ((auth == None) or (urls.get(url, None)[0] != auth)):
        print('unauthorized request')
        return ''

    # check how many remaining files
    if(urls[url][1] == 1):
        # remove url - pi pair from existing urls
        urls.pop(url)
    else:
        urls[url][1] -= 1 # remove 1 from file count

    # receive files
    # check if post request has the files
    if (('sensor_data_file' not in request.files) or 
            ('checksum' not in request.headers)):
        print('Required files not included')
        return ''

    # collect files
    datafile = request.files['sensor_data_file']
    checksum = request.headers['checksum']

    # check for empty fields / None
    if ((datafile.filename == '') or (checksum == '')):
        print('Empty file or checksum fields')
        return ''

    # check for allowed file extensions
    if (not allowed_file(datafile.filename)):
        print('wrong file type')
        return ''
    
    # create local names for files
    data_f_name = os.path.join(app.config['STORAGE_FOLDER'], secure_filename(auth + '_' + datafile.filename))
    name = datafile.filename.split('.')[0]
    checksum_f_name = os.path.join(app.config['STORAGE_FOLDER'], 
            secure_filename(auth + '_' + name + '.sha256'))

    # save data file
    datafile.save(data_f_name)
    
    # verify checksum
    chksm = verify_checksum(data_f_name, checksum)
    if chksm: # successful verification
        print('Checksum verified successfully')
        
        # save checksume file
        try:
            f = open(checksum_f_name, 'w')  # overwrites if file already exists
        except:
            f = open(checksum_f_name, 'a')  # creates file if doesn't exist
        f.write(checksum)
        f.write(' ' + auth + '_' + datafile.filename + '\n')
        f.close()

        # return success code
        return checksum

    else:
        print('Wrong checksum')
        # delete store file
        os.remove(data_f_name)

        # return error
        return ''
