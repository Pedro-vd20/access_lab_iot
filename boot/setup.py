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

import os
import sys
import requests as rqs
import time
import hashlib
import json

sys.path.append('/home/pi/')
from packages.modules import *

#----------

NAME='access'
URL = 'https://10.224.83.51:3500/'

#----------

# set up Pi as a router for user to connect to
def router_setup():
    # reset wpa file
    with open(f'{PATH}wpa_supplicant.conf', 'w') as f:   
        f.write('ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n' + \
            'update_config=1\ncountry=AE\n\n')

    # enable wireless access post
    run('sudo systemctl unmask hostapd')
    run('sudo systemctl enable hostapd')

    # define wireless configuration
    # check if already copied dhcpcd
    if not os.path.exists(f'{PATH}dhcpcd.conf.orig'):
        run(f'sudo mv /etc/dhcpcd.conf {PATH}dhcpcd.conf.orig')
    
    # copy original dhcpcd
    run(f'cp {PATH}dhcpcd.conf.orig {PATH}dhcpcd.conf')
    with open(PATH + 'dhcpcd.conf', 'a') as f:
        f.write('\ninterface wlan0\n\tstatic ip_address=192.168.4.1/24\n\t' + \
            'nohook wpa_supplicant\n')

    run(f'sudo mv {PATH}dhcpcd.conf /etc/dhcpcd.conf')

    # configure DHCP and DNS
    # check if already copied dnsmasq.conf
    if not os.path.exists(f'{PATH}dnsmasq.conf.orig'):
        run(f'sudo cp /etc/dnsmasq.conf {PATH}dnsmasq.conf.orig')
    
    # set up dhsmasq configuration
    with open(f'{PATH}dnsmasq.conf', 'w') as f:
        f.write('interface=wlan0\ndhcp-range=192.168.4.2,' + \
            '192.168.4.20,255.255.255.0,24h\n\ndomain=wlan\naddress=' + \
            '/gw.wlan/192.168.4.1')

    run(f'sudo mv {PATH}dnsmasq.conf /etc/dnsmasq.conf')

    # ensure wireless operation
    run('sudo rfkill unblock wlan')

    # configure hostapd software
    with open(PATH + 'hostapd.conf', 'w') as f:
        f.write('country_code=AE\ninterface=wlan0\nssid=')
        f.write(NAME)
        f.write('\nhw_mode=g\nchannel=7\nmacaddr_acl=0\n#auth_algs=1\n' + \
            'ignore_broadcast_ssid=0\nwpa=0\n#wpa=2\n#wpa_passphrase=' + \
            'password\n#wpa_key_mgmt=WPA-PSK\n#wpa_pairwise=TKIP\n' + \
            '#rsn_pairwise=CCMP\n') 
        #f.write('\nhw_mode=g\nchannel=7\nmacaddr_acl=0\nauth_algs=1\nignore_broadcast_ssid=0\n#wpa=0\nwpa=2\nwpa_passphrase=password\nwpa_key_mgmt=WPA-PSK\nwpa_pairwise=TKIP\nrsn_pairwise=CCMP\n')

    run(f'sudo mv {PATH}hostapd.conf /etc/hostapd/hostapd.conf')

    # enable dnsmasq in case disabled previously
    run('sudo systemctl enable dnsmasq') 

    log('Pi configured as wireless access point')

    # reboot system
    run('sudo systemctl reboot') 


# start flask server to collect wifi info
def start_flask():
    time.sleep(5)
    #run('sudo systemctl enable flask_app')
    run('sudo systemctl restart flask_app')
    log('Running Flask server')

# reverts the pi to connecting to the internet rather than acting as a router
def revert_router():
    # lets flask app finish running before rebooting pi
    time.sleep(2)

    # remove hostapd.conf
    run('sudo rm /etc/hostapd/hostapd.conf')

    # restore dnsmasq.conf
    run(f'sudo mv {PATH}dnsmasq.conf.orig /etc/dnsmasq.conf')

    # restore dhcpcd
    run(f'sudo mv {PATH}dhcpcd.conf.orig /etc/dhcpcd.conf')

    # disable hostapd and dnsmasq
    run('sudo systemctl disable dnsmasq')
    run('sudo systemctl disable hostapd')

    # move wpa supplicant
    run(f'sudo mv {PATH}networkconfig.txt /etc/wpa_supplicant/' + \
        'wpa_supplicant.conf')

    # reboot
    run('sudo systemctl reboot')

# throw an exception after enough time has passed
def handler(signum, frame):
    raise TimeoutError('Too long to respond')

def test_connection():
    # wait for network to connect and return an ip address
    time.sleep(30)

    while True:
        try:
            if register_box() != '200':
                raise(ConnectionError('Failed to register email'))
            log('Pi is connected to the internet, starting data collection')
            # if test network does not time out
            write_state(5)
            break
        except rqs.exceptions.RequestException:
            # connected to the router but timeout connecting to the internet
            log('The Pi could not connect')
            write_state(2)
            router_setup()
            exit(0)
        except ConnectionError:
            # server did not validate the data received, try send it again
            log('Response error from server')
            time.sleep(20)

    main() # if the function doesn't restart the pi and manages to escape the 
        # loop then the network should be verified



# sends collected email address to server and serves to test connection
def register_box():
    from station_id import secret

    # collect email
    with open(f'{PATH}email.txt', 'r') as f:
        email = f.readline().strip()
    
    url = URL + 'register/'
    headers = {'pi_id': secret, 'email': email}
    cert = f'{HOME}cert.pem'   

    # collect file detailing what sensors are on this box
    with open(f'{HOME}sensors_config.txt', 'rb') as f:
        hash_256 = hashlib.sha256(f.read()).hexdigest()

    files = {'sensor_config': open(f'{HOME}sensors_config.txt', 'rb')}
    headers['checksum'] = hash_256

    # send
    log('Sending email to register')
    rsp = rqs.post(url, verify=cert, headers=headers, files=files)
    return rsp.text


def main():
    # check state of machine
    try:
        # try read file with state
        f = open(PATH + STATE, 'r')
        state = int(f.readline().strip())
        f.close()
    except:
        # file not found, assume state is 0
        state = 1

    log('Current state: ' + str(state))

    if state == 1: # packages downloaded, Pi now needs to set up as a router
        write_state(2)
        router_setup()
    elif state == 2: # start up flask app
        # state will not change until form is submitted
        start_flask()
    elif state == 3: # pi must test connection to wifi
        write_state(4)
        log('Pi will stop serving as a wireless access point')
        revert_router()
    elif state == 4:
        log('Testing wifi connection')
        test_connection()
    # state 3 will keep Pi as wireless access point but test wifi
    # state 4 will revert pi as router
    # state 5 will start the detection and measurement
    elif state == 5:
       
        log('Starting data collection')
        time.sleep(20)
        run('sudo systemctl start diagnostics')
        run('python3 ' + HOME + 'data_collection.py')
        print('Working!')


if __name__ == '__main__':
    main()


