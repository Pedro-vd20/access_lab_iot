from flask import Flask, request, render_template, redirect
import os
import modules

##########

# go through a list of networks and remove duplicates
def filter_list(ls):
    unique = {}

    for x in ls:
        # elements in list stored as ESSID:"network_name"
        x = x.split('"')[1].strip() # retrieve network name
        print(x)
        # hidden networks appear as \x00, ignore those
        if '\\x00' not in x and unique.get(x, 1): # make sure x not in unique yet
            unique[x] = 0 # add to unique

    return list(unique.keys())

# create a wpa_supplicant file
def create_network_config(ssid, password, is_org, username=""):
    # overwrite / create file
    try:
        f = open(PATH + 'networkconfig.txt', 'w')
    except:
        f = open(PATH + 'networkconfig.txt', 'a')

    
    f.write('ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\nupdate_config=1\ncountry=AE\n\n')

    f.write('network={\n\tssid="')
    f.write(ssid)
    f.write('"\n')

    if is_org:
        f.write('\tproto=RSN\n\tkey_mgmt=WPA-EAP\n\teap=PEAP\n\tidentity="')
        f.write(username)
        f.write('"\n\tpassword="')
        f.write(password)
        f.write('"\n\tphase2="auth=MSCHAPV2"\n\tpriority=1\n')

    else:
        f.write('\tpsk="')
        f.write(password)
        f.write('"\n\tscan_ssid=1\n')

    f.write('}\n')
    f.close()



##########

app = Flask(__name__)

##########

@app.route('/', methods=['GET'])
def home():
    log('User accessing wifi survey site')
    
    # scan for available networks 
    run('sudo iwlist wlan0 scan | grep ESSID > ' + PATH + 'networks.txt')
    f = open(PATH + 'networks.txt', 'r')
    options = f.readlines() # each network is saved as ESSID:"name"
    f.close()
    
    # filter out repeated networks
    options = filter_list(options)

    # if no networks available, handle error
    if len(options) == 0:
        # HANDLE ERROR
        log('ERROR no networks found, informing user')
        return 'No networks detected, be sure Pi can connect to wifi'

    # print(type(txt))

    # collect possible error info
    # errors from phase 3 stored in network_diag.txt file, if any errors available
    try:
        f = open(PATH + 'network_diag.txt', 'r')
        error_info = f.readline()
        error = error_info != ''
    except:
        error = False
        error_info = ''

    '''
    1. Can't connect to network (no ip)
    2. Can't connect to wifi (can't send message out) 

    Info for no ip -> /etc/wpa_supplicant/wpa_supplicant.conf
    Info for no wifi -> $ ip a | grep wlan0
    '''

    return render_template('index.html', wifi_list=options, error=error, error_info=error_info)


@app.route('/connect/', methods=['POST'])
def handle_form():
    # collect form data
    network = request.form['network']
    n_type = (request.form['type'] == 'organization') # network type is organization
    password = request.form['pass']
    password_2 = request.form['pass2']
    user = "" if not n_type else request.form['user'] # collect user only if network type is organization

    # check matching passwords
    if (password != password_2):
        # write error into file
        log('Passwords did not match, returning to form')
        try:
            f = open('/home/pi/network_diag.txt', 'w')
        except:
            f = open('home/pi/network_diag.txt', 'a')
        f.write('Passwords do not match')
        f.close()

        # ignore form input, redirect to main page with new error
        return redirect('/') 

    log('Form received, attempting to connect to ' + network)

    # create network config file
    create_network_config(network, password, n_type, user)

    write_state(3) # update state to network testing phase

    # revert py into non-access point mode
    run('python3 ' + PATH + 'setup.py')

    return 'The Pi is trying to connect, if in a few minutes you can still connect to the \'access\' wifi, there was an error.'



app.run(host='192.168.4.1', port=3500)

