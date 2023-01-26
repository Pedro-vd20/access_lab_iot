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

from flask import Flask, request, render_template, redirect
import os
import sys

sys.path.append('/home/pi/')

import packages.modules as modules

#----------

'''
iterate through a list of networks and returns list with no duplicates
list elements must contained desired info inside "" (split will extract it)
Sample ls input:
    ['ESSID:"nyu"', 'ESSID:"eduroam", 'ESSID:"nyuadguest"']
'''
def filter_list(ls):
    unique = set()

    for x in ls:
        # elements in list stored as ESSID:"network_name"
        x = x.split('"')[1].strip() # retrieve network name
        print(x)
        # hidden networks appear as \x00, ignore those
        if '\\x00' not in x and x not in unique: # make sure x not in unique yet
            unique.add(x) # add to unique

    return list(unique)

'''
Creates the wpa_supplicant file for the pi to connect to wifi
Supports connecting to password protected wifi and connecting to 
    organization networks that require further username and password 
    authentication
'''
def create_network_config(ssid, password, is_org, username=""):
    # create supplicant file
    with open(os.path.join(modules.PATH, 'networkconfig.txt'), 'w') as f:
        f.write('ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n' + \
            'update_config=1\ncountry=AE\n\nnetwork={\n\tssid="' + f'{ssid}"\n')

        # organization wifi requires to add username and password, not just password
        if is_org:
            f.write('\tproto=RSN\n\tkey_mgmt=WPA-EAP\n\teap=PEAP\n\tidentity="' + \
                f'{username}"\n\tpassword="{password}"\n\tphase2="auth=' + \
                'MSCHAPV2"\n\tpriority=1\n')
        else:
            f.write(f'\tpsk="{password}"\n\tscan_ssid=1\n')

        f.write('}\n')
    
#----------

app = Flask(__name__)

#----------

'''
Main page is a form requesting the user critical info about available wifi 
    networks to connect to. 
Before returning page, must scan all available wifi networks for the user to 
    choose which to connect to and provide required info
'''
@app.route('/', methods=['GET'])
def home():
    modules.log('User accessing wifi survey site')
    
    # scan for available networks 
    os.system(f'sudo iwlist wlan0 scan | grep ESSID > {os.join(modules.PATH, "networks.txt")}')
    with open(os.path.join(modules.PATH, 'networks.txt'), 'r') as f:
        options = f.readlines() # each network is saved as ESSID:"name"
    
    # filter out repeated networks
    options = filter_list(options)

    # if no networks available, handle error
    if len(options) == 0:
        # HANDLE ERROR
        modules.log('ERROR no networks found, informing user')
        return render_template('no_networks.html')

    # print(type(txt))

    # collect possible error info
    # errors from phase 3 stored in network_diag.txt file, if any errors available
    with open(os.path.join(modules.PATH, 'network_diag.txt'), 'r') as f:
        error_info = f.readline()
        error = error_info != ''


    '''
    1. Can't connect to network (no ip)
    2. Can't connect to wifi (can't send message out) 

    Info for no ip -> /etc/wpa_supplicant/wpa_supplicant.conf
    Info for no wifi -> $ ip a | grep wlan0
    '''

    return render_template('index.html', wifi_list=options, error=error, error_info=error_info)

'''
Stores the information the user inputs about their own network for the pi to 
    connect to.
Does some minor checking (passwords match)
Collects user email
Resets pi to attempt to use this info to connect to the wifi
'''
@app.route('/connect/', methods=['POST'])
def handle_form():
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
        modules.log('Passwords did not match, returning to form')
        with open(os.path.join(modules.PATH, 'network_diag.txt'), 'w') as f:
            f.write('Passwords do not match')

        # ignore form input, redirect to main page with new error
        return redirect('/') 

    modules.log(f'Form received, attempting to connect to {network}')

    # store email for later
    with open(os.path.join(modules.PATH, 'email.txt'), 'w') as f:
        f.write(email)

    # create network config file
    create_network_config(network, password, n_type, user)

    modules.write_state(3) # update state to network testing phase

    # revert py into non-access point mode
    os.system(f'python3 {os.path.join(modules.PATH, "setup.py")}')

    return render_template('testing_wifi.html')

#----------


app.run(host='192.168.4.1', port=3500)
#app.run()

