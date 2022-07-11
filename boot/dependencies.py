from modules import *

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
