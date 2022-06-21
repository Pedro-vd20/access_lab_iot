import os

def run(arg):
    return os.system(arg)

def main():
    run('sudo apt update')
    run('sudo apt upgrade')
    run('sudo apt-get install python3-pip')
    run('sudo apt-get install hostapd')
    run('sudo apt-get install dnsmasq')
    run('sudo DEBIAN_FRONTEND=noninteractive apt install -y netfilter-persistent iptables-persistent')

    try:
        f = open('wpa_supplicant.conf', 'w')
    except:
        f = open('wpa_supplicant.conf', 'a')
    
    f.write('ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\nupdate_config=1\ncountry=AE\n\n')


    f.close()

    run('sudo mv wpa_supplicant.conf /etc/wpa_supplicant/')

    run('sudo systemctl reboot')


if __name__ == '__main__':
    main()
