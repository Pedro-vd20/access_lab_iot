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

#any file with a different extension will be silently discarded
ALLOWED_EXTENSIONS = {'txt', 'sha256'}
#'STORAGE_FOLDER' is the place where the files are permanently stored.
STORAGE_FOLDER = '/home/pedro/Desktop/'
#'UPLOAD_FOLDER' is a transit area where files are saved while checksumming
UPLOAD_FOLDER = '/home/pedro/Documents/iot_internship/receiver/'

app = Flask(__name__)
app.config['SECRET_KEY'] = '1234567'
app.config['MAX_CONTENT_LENGTH'] = 1024 * 128 #128Kbyte max filesize. 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#---------------------------------------------------------

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def verify_checksum(fname, chksm):
    with open(fname, 'rb') as f:
        hash = hashlib.sha256(f.read()).hexdigest()
    if hash == chksm:
        return hash
    else:
        return None

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        print(request.data)

        # check if the post request has the file part
        if (('sensor_data_file' not in request.files) or
            ('checksum'         not in request.files)):
            return 'No file part'
            #flash('No file part')
            #return redirect(request.url)
        datafile = request.files['sensor_data_file']
        checksum = request.files['checksum']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if (datafile.filename=='') or (checksum.filename==''):
            return 'No selected file'
            #flash('No selected file')
            #return redirect(request.url)
        if (datafile and allowed_file(datafile.filename) and
            checksum and allowed_file(checksum.filename)):
            datafilename = os.path.join(app.config['UPLOAD_FOLDER'],
                                        secure_filename(datafile.filename))
            checksumname = os.path.join(app.config['UPLOAD_FOLDER'],
                                        secure_filename(checksum.filename))
            datafile.save(datafilename)
            checksum.save(checksumname)
            chksm = verify_checksum(datafilename, checksumname)
            ### Add further sanification here ###
            ### E.g. check for the presence of a valid station ID hash ###
            if chksm is None: #remove files that don't checksum.
                os.remove(datafilename)
                os.remove(checksumname)
                return 'Unmatched checksum'
            else: #save in 'STORAGE_FOLDER' files that checksum.
                os.rename(datafilename,
                          os.path.join(STORAGE_FOLDER,
                                       os.path.split(datafilename)[1]))
                os.rename(checksumname,
                          os.path.join(STORAGE_FOLDER,
                                       os.path.split(checksumname)[1]))
                return chksm
            #return redirect(url_for('upload_file', name=datafilename))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=sensor_data_file placeholder="Choose file">
      <input type=file name=checksum placeholder="Choose checksum">
      <input type=submit value=Upload>
    </form>
    '''
