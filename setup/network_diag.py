import os
import requests as rqs
import signal
import time

def handler(signum, frame):
    print('timeout!')
    raise Exception('Too long to respond')

def run(arg):
    os.system(arg)

def test_network():
    rqs.get('http://google.com')
    return 0

def main():
    time.sleep(30)
    # test for IP address
    run('ip a | grep wlan0 > /home/pi/network_diag.txt')

    f = open('/home/pi/network_diag.txt', 'r')
    text = ''.join(f.readlines())
    f.close()

    f = open('/home/pi/network_diag.txt', 'w')
    state = open('/home/pi/state.txt', 'w')

    if 'NO-CARRIER' in text:
        print('No IP')
        f.write('Failed to connect to the network. Make sure the password is correct')
        state.write('1')
        state.close()
        f.close()
        run('python3 /home/pi/setup.py')
        exit(0)

    signal.signal(signal.SIGALRM, handler)
    signal.alarm(30)

    try:
        test_network()
        print('Success!')
        state.write('4')
        state.close()
        f.close()
        run('python3 /home/pi/setup.py')
        #exit(0)
    except:
        f.write('The Pi could connect to the wifi but has no access to the internet. Be sure your wifi connection is working properly')
        state.write('1')
        f.close()
        state.close()
        #exit(0)
        print('Could not connect')
        run('python3 /home/pi/setup.py')

    
if __name__ == '__main__':
    main()
