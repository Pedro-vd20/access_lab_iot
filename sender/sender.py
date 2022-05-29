import requests as rqs
import os
import hashlib
from secret import secret

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

URL = 'http://10.225.5.51:5000'
FOLDER = '/home/pi/logs/'
DEST_FOLDER = '/home/pi/sent_files/'

def main():
    # check how many files need to be sent
    dir_list = os.listdir(FOLDER)
    num_files = len(dir_list)

    # send authentication request to server
    headers = {'pi_id': secret, 'num_files': num_files}
    response = rqs.get(URL, headers=headers).text.strip()

    print(response)

    # check if response is a success
    if(response == ''): # empty response means error
        print("Response failed, ending program")
        return -1    # FIGURE OUT WHAT TO DO HERE
        # here we must set some flag to indicate the sending failed for this file

    # loop through all files
    for file in dir_list:
        # get hash
        with open(file, 'rb') as f:
            hash_256 = hashlib.sha256(f.read()).hexdigest()
            headers['checksum'] = hash_256

        # collect file
        files = {'sensor_data_file': open(file, 'rb')}

        # send request
        response = rqs.post(URL + '/upload/' + response[1], 
                    files=files, headers=headers).text.strip()

        print(response)

        files['sensor_data_file'].close()

        # check if success
        if (response == hash_256):
            # move file to sent folder
            os.system('mv ' + FOLDER + file + ' ' + DEST_FOLDER)



if __name__ == "__main__":
    main()
