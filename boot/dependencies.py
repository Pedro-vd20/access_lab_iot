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

import sys

sys.path.append('/home/pi/')

from packages.modules import *

# install python package
def p_install(pkg):
    run('pip3 install ' + pkg)

def install(sft):
    run('sudo apt-get install -y ' + sft)

def main():
    # install all python dependencies
    p_install('Flask')
    p_install('pyserial')
    p_install('pigpio')
    p_install('pynmea')
    p_install('pynmea2')
    p_install('adafruit-circuitpython-bme280')
    p_install('adafruit-circuitpython-ms8607')

    # install apt-get dependencies
    install('hostapd')
    install('dnsmasq')
    install('pigpiod')

    log('All dependencies installed')

    # set up dependencies
    run('sudo DEBIAN_FRONTEND=noninteractive apt install -y netfilter-persistent iptables-persistent')

    # set up services
    run('sudo systemctl start pigpiod')
    #run('sudo systemctl enable pigpiod')

    # move services
    run('sudo cp ' + PATH + 'services/* /lib/systemd/system/')
    # enable services
    run('sudo systemctl enable setup')
    run('sudo systemctl enable pigpiod')

    log('All services enabled')

    # create state.txt file
    try:
        f = open(PATH + 'state.txt', 'w')
    except:
        f = open(PATH + 'state.txt', 'a')

    f.write('1')
    f.close()

    log('State file created')

if __name__ == '__main__':
    main()
