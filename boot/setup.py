import os
import sys
import requests as rqs
import time
#import modules
from modules import *
import signal

NAME='access'
URL = 'https://10.224.83.51:3500/'

# set up Pi as a router for user to connect to
def router_setup():
    # reset wpa file
    file_path = PATH + 'wpa_supplicant.conf'
    try:
        f = open(file_path, 'w')
    except:
        f = open(file_path, 'a')
    
    f.write('ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\nupdate_config=1\ncountry=AE\n\n')
    f.close()


    # enable wireless access post
    run('sudo systemctl unmask hostapd')
    run('sudo systemctl enable hostapd')

    # define wireless configuration
    # check if already copied dhcpcd
    try:
        f = open(PATH + 'dhcpcd.conf.orig', 'r')
        f.close()
    except:
        run('sudo mv /etc/dhcpcd.conf ' + PATH + 'dhcpcd.conf.orig')
    
    # copy original dhcpcd
    run('cp ' + PATH + 'dhcpcd.conf.orig ' + PATH + 'dhcpcd.conf')
    f = open(PATH + 'dhcpcd.conf', 'a')
    f.write('\ninterface wlan0\n\tstatic ip_address=192.168.4.1/24\n\tnohook wpa_supplicant\n')
    f.close()

    run('sudo mv ' + PATH + 'dhcpcd.conf /etc/dhcpcd.conf')

    # configure DHCP and DNS
    # check if already copied dnsmasq.conf
    try:
        f = open(PATH + 'dnsmasq.conf.orig', 'r')
        f.close()
    except:
        run('sudo cp /etc/dnsmasq.conf ' + PATH + 'dnsmasq.conf.orig')
    
    # set up dhsmasq configuration
    try:
        f = open(PATH + 'dnsmasq.conf', 'w')
    except:
        f = open(PATH + 'dnsmasq.conf', 'a')
    f.write('interface=wlan0\ndhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h\n\ndomain=wlan\naddress=/gw.wlan/192.168.4.1')
    f.close()

    run('sudo mv ' + PATH + 'dnsmasq.conf /etc/dnsmasq.conf')

    # ensure wireless operation
    run('sudo rfkill unblock wlan')

    # configure hostapd software
    try:
        f = open(PATH + 'hostapd.conf', 'w')
    except:
        f = open(PATH + 'hostapd.conf', 'a')
    f.write('country_code=AE\ninterface=wlan0\nssid=')
    f.write(NAME)
    f.write('\nhw_mode=g\nchannel=7\nmacaddr_acl=0\n#auth_algs=1\nignore_broadcast_ssid=0\nwpa=0\n#wpa=2\n#wpa_passphrase=password\n#wpa_key_mgmt=WPA-PSK\n#wpa_pairwise=TKIP\n#rsn_pairwise=CCMP\n') 
    #f.write('\nhw_mode=g\nchannel=7\nmacaddr_acl=0\nauth_algs=1\nignore_broadcast_ssid=0\n#wpa=0\nwpa=2\nwpa_passphrase=password\nwpa_key_mgmt=WPA-PSK\nwpa_pairwise=TKIP\nrsn_pairwise=CCMP\n')
    f.close()

    run('sudo mv ' + PATH + 'hostapd.conf /etc/hostapd/hostapd.conf')

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
    run('sudo mv ' + PATH + 'dnsmasq.conf.orig /etc/dnsmasq.conf')

    # restore dhcpcd
    run('sudo mv ' + PATH + 'dhcpcd.conf.orig /etc/dhcpcd.conf')

    # disable hostapd and dnsmasq
    run('sudo systemctl disable dnsmasq')
    run('sudo systemctl disable hostapd')

    # move wpa supplicant
    run('sudo mv ' + PATH + 'networkconfig.txt /etc/wpa_supplicant/wpa_supplicant.conf')

    # reboot
    run('sudo systemctl reboot')

# throw an exception after enough time has passed
def handler(signum, frame):
    raise Exception('Too long to respond')

def test_connection():
    # wait for network to connect and return an ip address
    time.sleep(30)
    # test for IP address
    run('ip a | grep wlan0 > ' + PATH + 'network_diag.txt')
    log('Collecting IP')

    f = open(PATH + 'network_diag.txt', 'r')
    text = ''.join(f.readlines())
    f.close()

    f = open(PATH + 'network_diag.txt', 'w')

    if 'NO-CARRIER' in text: # no ip detected
        log('Could not connect to wifi, reverting to wireless access network')
        f.write('Failed to connect to the network. Make sure the password is correct')
        f.close()
        
        # reboot pi and change settings
        write_state(2)
        router_setup()
        exit(0)

    signal.signal(signal.SIGALRM, handler)
    signal.alarm(10) # set timeout timer for request

    try:
        if register_email() != '200':
            raise(Exception('Failed to register email'))
        log('Pi is connected to the internet, starting data collection')
        signal.alarm(0) # turn off alarm
        # if test network does not time out
        write_state(5)
    except:
        # connected to the router but timeout connecting to the internet
        f.write('The Pi could connect to the wifi but has no access to the internet. Be sure your wifi connection is working properly')
        write_state(2)
        log('Pi connected to the router but has no access to wifi')
        router_setup()

    f.close()


# sends collected email address to server and serves to test connection
def register_email():
    sys.path.append(HOME)
    from station_id import secret

    # collect email
    with open(PATH + 'email.txt', 'r') as f:
        email = f.readline().strip()
    
    url = URL + 'register/'
    headers = {'pi_id': secret, 'email': email}
    cert = HOME + 'cert.pem'

    # send
    log('Sending email to register')
    rsp = rqs.post(url, verify=cert, headers=headers)
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


