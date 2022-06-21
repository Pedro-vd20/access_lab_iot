import os
import requests as rqs
import time

STATE = '/home/pi/state.txt'
NAME = 'access'

# write new state to file
def write_state(num):
    try:
        f = open(STATE, 'w')
    except:
        f = open(STATE, 'a')
    f.write(str(num))
    f.close()


# run string on terminal
def run(arg):
    return os.system(arg)


# install necessary packages to run program
def wifi_setup():
    # install hostapd, dnsmasq, pip3, flask
    run('sudo apt update')
    run('sudo apt upgrade')
    run('sudo apt-get install python3-pip')
    run('pip3 install Flask')
    run('sudo apt-get install hostapd')
    run('sudo apt-get install dnsmasq')
    run('sudo DEBIAN_FRONTEND=noninteractive apt install -y netfilter-persistent iptables-persistent')

    # reset wpa file
    file_path = '/home/pi/wpa_supplicant.conf'
    try:
        f = open(file_path, 'w')
    except:
        f = open(file_path, 'a')
    
    f.write('ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\nupdate_config=1\ncountry=AE\n\n')
    f.close()

    run('sudo mv /home/pi/wpa_supplicant.conf /etc/wpa_supplicant/')

    # reboot system
    run('sudo systemctl reboot')


# set up Pi as a router for user to connect to
def router_setup():
    # scan available networks
    #os.system('sudo iwlist wlan0 scan | grep ESSID > networks.txt')

    # enable wireless access post
    run('sudo systemctl unmask hostapd')
    run('sudo systemctl enable hostapd')

    # define wireless configuration
    # check if already copied dhcpcd
    try:
        f = open('dhcpcd.conf.orig', 'r')
        f.close()
    except:
        run('sudo mv /etc/dhcpcd.conf /home/pi/dhcpcd.conf.orig')
    
    # copy original dhcpcd
    run('cp /home/pi/dhcpcd.conf.orig /home/pi/dhcpcd.conf')
    f = open('/home/pi/dhcpcd.conf', 'a')
    f.write('\ninterface wlan0\n\tstatic ip_address=192.168.4.1/24\n\tnohook wpa_supplicant\n')
    f.close()

    run('sudo mv /home/pi/dhcpcd.conf /etc/dhcpcd.conf')

    # configure DHCP and DNS
    # check if already copied dnsmasq.conf
    try:
        f = open('/home/pi/dnsmasq.conf.orig', 'r')
        f.close()
    except:
        run('sudo cp /etc/dnsmasq.conf /home/pi/dnsmasq.conf.orig')
    
    # set up dhsmasq configuration
    try:
        f = open('/home/pi/dnsmasq.conf', 'w')
    except:
        f = open('/home/pi/dnsmasq.conf', 'a')
    f.write('interface=wlan0\ndhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h\n\ndomain=wlan\naddress=/gw.wlan/192.168.4.1')
    f.close()

    run('sudo mv /home/pi/dnsmasq.conf /etc/dnsmasq.conf')

    # ensure wireless operation
    run('sudo rfkill unblock wlan')

    # configure ap software
    f = open('/home/pi/hostapd.conf', 'a')
    f.write('country_code=AE\ninterface=wlan0\nssid=')
    f.write(NAME)
    f.write('\nhw_mode=g\nchannel=7\nmacaddr_acl=0\n#auth_algs=1\nignore_broadcast_ssid=0\nwpa=0\n#wpa=2\n#wpa_passphrase=password\n#wpa_key_mgmt=WPA-PSK\n#wpa_pairwise=TKIP\n#rsn_pairwise=CCMP\n') 
    #f.write('\nhw_mode=g\nchannel=7\nmacaddr_acl=0\nauth_algs=1\nignore_broadcast_ssid=0\n#wpa=0\nwpa=2\nwpa_passphrase=password\nwpa_key_mgmt=WPA-PSK\nwpa_pairwise=TKIP\nrsn_pairwise=CCMP\n')
    f.close()

    run('sudo mv /home/pi/hostapd.conf /etc/hostapd/hostapd.conf')

    # enable dnsmasq in case disabled previously
    run('sudo systemctl enable dnsmasq') 

    # reboot system
    run('sudo systemctl reboot') 


# start flask server to collect user info
def start_flask():
    debug('About to start app')
    time.sleep(5)
    #run('sudo systemctl enable flask_app')
    run('sudo systemctl restart flask_app')
    #time.sleep(5)
    #run('sudo systemctl start flask_app')
    # flask server will be in charge
    # of chaning state after submission
    debug('Flask app is running')


# revert pi to stop acting as wireless access point 
def revert_router():
    # remove hostapd.conf
    run('sudo rm /etc/hostapd/hostapd.conf')

    # restore dnsmasq.conf
    run('sudo mv /home/pi/dnsmasq.conf.orig /etc/dnsmasq.conf')

    # restore dhcpcd
    run('sudo mv /home/pi/dhcpcd.conf.orig /etc/dhcpcd.conf')

    # disable hostapd and dnsmasq
    run('sudo systemctl disable dnsmasq')
    run('sudo systemctl disable hostapd')

    # move wpa supplicant
    run('sudo mv /home/pi/networkconfig.txt /etc/wpa_supplicant/wpa_supplicant.conf')

    # reboot
    run('sudo systemctl reboot')

# debug and ask for input
def debug(msg):
    f = open('/home/pi/debug.txt', 'a')
    f.write(msg + '\n')
    f.close()
    #y = input(msg + ' [Y/n]')
    #print('hello')


def main():
    # check state of machine
    try:
        # try read file with state
        f = open(STATE, 'r')
        state = int(f.readline().strip())
        f.close()
    except:
        # file not found, assume state is 0
        state = 0

    print('Current state:', state)
    debug('Continue?')

    if state == 0: # no setup, py is at the lab and is connected to the internet
        # modify state
        write_state(1)
        debug('State set to 1, about to set up wifi installs')
        wifi_setup() # download and install packages
    elif state == 1: # packages downloaded, Pi now needs to set up as a router
        write_state(2)
        debug('State set to 2, about to set up Pi as router')
        router_setup()
    elif state == 2: # start up flask app
        debug('State won\'t be changed, starting flask app')
        # state will not change until form is submitted
        start_flask()
    elif state == 3: # pi must test connection to wifi
        debug('Testing wifi connection')
        run('python3 /home/pi/network_diag.py')
    # state 3 will keep Pi as wireless access point but test wifi
    # state 4 will revert pi as router
    # state 5 will start the detection and measurement
    elif state == 4:
        debug('Starting "server"')
        f = open('/home/pi/log.txt', 'a')
        f.write('hello there\n')
        f.close()
        print('Working!')


if __name__ == '__main__':
    main()


