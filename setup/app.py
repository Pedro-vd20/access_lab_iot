from flask import Flask, request, render_template, redirect
import os

##########
f = open('/home/pi/testing.txt', 'a')
f.write('Hello there\n')
f.close()

app = Flask(__name__)

def run(arg):
    return os.system(arg)

def filter_list(ls):
    unique = {}

    for x in ls:
        x = x.split('"')[1].strip()
        print(x)
        if '\\x00' not in x and unique.get(x, 1):
            unique[x] = 0

    return list(unique.keys())


@app.route('/', methods=['GET'])
def home():
    
    os.system('sudo iwlist wlan0 scan | grep ESSID > networks.txt')
    f = open('/home/pi/networks.txt', 'r')
    options = f.readlines()
    f.close()

    options = filter_list(options)

    if len(options) == 0:
        # HANDLE ERROR
        return 'No networks detected, be sure Pi can connect to wifi'

    # print(type(txt))

    # collect possible error info
    try:
        f = open('network_diag.txt', 'r')
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
    n_type = (request.form['type'] == 'organization')
    password = request.form['pass']
    password_2 = request.form['pass2']

    if (password != password_2):
        # write error into file
        try:
            f = open('/home/pi/network_diag.txt', 'w')
        except:
            f = open('home/pi/network_diag.txt', 'a')
        f.write('Passwords do not match')
        f.close()

        return redirect('/')
    
    # create network file
    try:
        f = open('/home/pi/networkconfig.txt', 'w')
    except:
        f = open('/home/pi/networkconfig.txt', 'a')

    f.write('ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\nupdate_config=1\ncountry=AE\n\n')

    f.write('network={\n\tssid="')
    f.write(network)
    f.write('"\n')

    if n_type:
        user = request.form['user']

        f.write('\tproto=RSN\n\tkey_mgmt=WPA-EAP\n\teap=PEAP\n\tidentity="')
        f.write(user)
        f.write('"\n\tpassword="')
        f.write(password)
        f.write('"\n\tphase2="auth=MSCHAPV2"\n\tpriority=1\n')

    else:
        f.write('\tpsk="')
        f.write(password)
        f.write('"\n\tscan_ssid=1\n')

    f.write('}\n')
    f.close()
    
    try:
        f = open('state.txt', 'w')
    except:
        f = open('state.txt', 'a')
    f.write('3')
    f.close()

    #revert_router()
    #run()
    run('python3 /home/pi/revert.py')

    return 'The Pi is trying to connect, if in a few minutes you can still connect to the \'access\' wifi, there was an error.'



app.run(host='192.168.4.1', port=3500) # also run https???
# limit num people on network to just 1 (security????)


