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

import requests as rqs
import sys
import os
import hashlib
import packages.modules as modules

try:
    import station_id as station
except ModuleNotFoundError:
    raise(ModuleNotFoundError('Pi ID could not be found'))

'''def main():

    # myobj = {'data': "Hello there"}
    # obj2 = {'data': 'This is second option'}
    URL = 'http://10.225.5.51:5000/'
    # URL = "http://albert.nyu.edu"

    fname = 'test.txt'


    with open(fname, 'rb') as f:
        hash_256 = hashlib.sha256(f.read()).hexdigest()
        print("Local hash:", hash_256)

    files = {'sensor_data_file': open(fname, 'rb')}
    data = {'checksum': hash_256}

    r = rqs.post(URL, files=files, headers=data)
    print(r.text)
    # MUST CHECK THAT CHECKSUM IS VALID!
    # PROTOCOL FOR SENDER TO RESEND DATA 
    # MODIFY SENDER AND RECEIVER SO THAT EACH PI GETS ITS OWN CHANNEL


    # SENDER WILL NOT HAVE CHECKSUM FILES BUT RECEIVER SHOULD STILL STORE THEM
'''

# URL = 'http://10.224.83.51:5000'
# FOLDER = '/home/pi/data_logs/'
# DEST_FOLDER = '/home/pi/sent_files/'

def main(args):
    # collect arg info
    if (len(args) < 4):
        print(len(args))
        modules.log('Missing arguments, stopping sender')
        return -1 
    
    URL = f'https://{args[1]}:3500/upload'
    FOLDER = args[2]
    VERIFY = os.path.join(modules.HOME, 'cert.pem')

    # check how many files need to be sent
    if not os.path.isdir(FOLDER):
        modules.log(f'{FOLDER} not a valid directory, stopping sender')
        return -1

    dir_list = sorted(os.listdir(FOLDER))
    num_files = len(dir_list)

    # send authentication request to server
    headers = {'pi_id': station.secret, 'pi_num': station.station_num}
    try:    
        response = rqs.get(URL, headers=headers, verify=VERIFY).text.strip()
    except rqs.exceptions.RequestException:
        modules.log(f'{URL} can\'t be reached, stopping sender')
        return -1
    
    print(response)

    # check if response is a success
    if(response == '401'): # empty response means error
        modules.log("Sender authentication failed")
        return -1    # FIGURE OUT WHAT TO DO HERE
        # here we must set some flag to indicate the sending failed for this file
    
    # collect url from the response 301 new_url
    response = response.strip().split(' ')[1]

    # check if dest folder exists
    DEST_FOLDER = os.path.join(FOLDER, '../sent_files/')
    if not os.path.isdir(DEST_FOLDER):
        os.mkdir(DEST_FOLDER)
    
    # loop through all files
    modules.log('Sending files')
    for send_file in dir_list:
        # get hash
        with open(os.path.join(FOLDER, send_file), 'rb') as f:
            hash_256 = hashlib.sha256(f.read()).hexdigest()
            headers['checksum'] = hash_256

        headers['num_files'] = str(num_files) # send server num of files left to send

        # collect file
        files = {'sensor_data_file': open(os.path.join(FOLDER, send_file), 'rb')}

        # send request
        try:
            rsp = rqs.post(os.path.join(URL, response), 
                    files=files, headers=headers, verify=VERIFY).text.strip()
        except rqs.exceptions.RequestException:
            modules.log(f'{os.path.join(URL, "upload", response)} can\'t be reached')
            return -1

        files['sensor_data_file'].close()

        # check if success
        if (rsp == '200'):
            # move file to sent folder
            os.system(f'mv {os.path.join(FOLDER, send_file)} {DEST_FOLDER}')
            modules.log(f'{send_file} sent')
        else:
            modules.log(f'{send_file} could not be sent')

        num_files -= 1

    return 0
        



if __name__ == "__main__":
    main(sys.argv)
