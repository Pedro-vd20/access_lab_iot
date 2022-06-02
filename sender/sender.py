import requests as rqs
import sys
import os
import hashlib

try:
    from secret import secret
except:
    print('PI id not found')
    exit(-1)

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
# FOLDER = '/home/pi/logs/'
# DEST_FOLDER = '/home/pi/sent_files/'

def main(args):
    # collect arg info
    if (len(args) < 3):
        print(len(args))
        print('Missing arguments')
        return -1 
    
    URL = 'https://' + args[1] + ':3500'
    FOLDER = args[2]

    # check how many files need to be sent
    try:    
        dir_list = os.listdir(FOLDER)
    except:
        print(FOLDER, 'not a valid directory')
        return -1
    num_files = len(dir_list)

    # send authentication request to server
    headers = {'pi_id': secret}
    try:    
        response = rqs.get(URL, headers=headers).text.strip()
    except:
        print(URL, 'can\'t be reached')
        return -1
    
    print(response)

    # check if response is a success
    if(response == ''): # empty response means error
        print("Authentication failed")
        return -1    # FIGURE OUT WHAT TO DO HERE
        # here we must set some flag to indicate the sending failed for this file

    # check if dest folder exists
    DEST_FOLDER = FOLDER + '../sent_files/'
    try:
        os.listdir(DEST_FOLDER)
    except:
        os.system('mkdir ' + DEST_FOLDER)


    # loop through all files
    for file in dir_list:
        # get hash
        with open(FOLDER + file, 'rb') as f:
            hash_256 = hashlib.sha256(f.read()).hexdigest()
            headers['checksum'] = hash_256

        headers['num_files'] = str(num_files) # send server num of files left to send

        # collect file
        files = {'sensor_data_file': open(FOLDER + file, 'rb')}

        # send request
        try:
            checksum = rqs.post(URL + '/upload/' + response, 
                    files=files, headers=headers).text.strip()
        except:
            print(URL + '/upload/' + response, 'can\'t be reached')
            return -1

        print(response)

        files['sensor_data_file'].close()

        # check if success
        if (checksum == hash_256):
            # move file to sent folder
            os.system('mv ' + FOLDER + file + ' ' + DEST_FOLDER)
        else:
            print(file, 'could not be sent')

        num_files -= 1
        



if __name__ == "__main__":
    main(sys.argv)
