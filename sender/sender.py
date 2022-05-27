import requests as rqs
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
FILE = 'test.txt'

def main():
    # send authentication request to server
    headers = {'pi_id': secret}
    response = rqs.get(URL, headers=headers).text.split('\n')

    print(response)

    # check if response is a success
    if(response[0][:3] != '302'): # 302 is the success code
        print("Response failed, ending program")
        return -1    # FIGURE OUT WHAT TO DO HERE
        # here we must set some flag to indicate the sending failed for this file

    # get hash
    with open(FILE, 'rb') as f:
        hash_256 = hashlib.sha256(f.read()).hexdigest()
        headers['checksum'] = hash_256

    # collect file
    files = {'sensor_data_file': open(FILE, 'rb')}

    # send request
    response = rqs.post(URL + '/upload/' + response[1], 
                files=files, headers=headers).text.split('\n')

    print(response)

    files['sensor_data_file'].close()

    # check if success
    if response[0][:3] != '200':
        print("File sending failed")
        return -1

    elif response[1] == hash_256:
        print("Success! Hash matched")
        return 0

    print("Transfer failed")
    return -1







if __name__ == "__main__":
    main()
