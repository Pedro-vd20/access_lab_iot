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

from flask import Flask, request, render_template, redirect
import os
import sys

sys.path.append('/home/pi/')

from packages.modules import *

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
        return render_template('no_networks.html')

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
    print('here')
    # collect form data
    email = request.form['email']
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
            f = open(PATH + 'network_diag.txt', 'w')
        except:
            f = open(PATH + 'network_diag.txt', 'a')
        f.write('Passwords do not match')
        f.close()

        # ignore form input, redirect to main page with new error
        return redirect('/') 

    log('Form received, attempting to connect to ' + network)

    # store email for later
    try:
        f = open(PATH + 'email.txt', 'w')
    except:
        f = open(PATH + 'email.txt', 'a')
    f.write(email)

    # create network config file
    create_network_config(network, password, n_type, user)

    write_state(3) # update state to network testing phase

    # revert py into non-access point mode
    run('python3 ' + PATH + 'setup.py')

    return render_template('testing_wifi.html')

app.run(host='192.168.4.1', port=3500)
#app.run()

