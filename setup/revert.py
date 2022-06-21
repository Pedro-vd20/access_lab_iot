import os
import time

# reverts the pi to connecting to the internet rather than acting as a router

def run(arg):
    return os.system(arg)

def main():
    # lets flask app return previous page
    time.sleep(2)

    # remove hostapd.conf
    run('sudo rm /ett/hostapd/hostapd.conf')

    # restore dnsmasq.conf
    run('sudo mv dnsmasq.conf.orig /etc/dnsmasq.conf')

    # restore dhcpcd
    run('sudo mv dhcpcd.conf.orig /etc/dhcpcd.conf')

    # disable hostapd and dnsmasq
    run('sudo systemctl disable dnsmasq')
    run('sudo systemctl disable hostapd')

    # move wpa supplicant
    run('sudo mv networkconfig.txt /etc/wpa_supplicant/wpa_supplicant.conf')

    # reboot
    run('sudo systemctl reboot')


if __name__ == '__main__':
    main()
