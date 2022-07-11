import os
import datetime

# shared code for multiple files

##########
# Constants
##########

STATE = 'state.txt'
PATH = '/home/pi/boot/'
HOME = '/home/pi/'

##########
# Code
##########

# makes running console commands easier
def run(arg):
    os.system(arg)

# write new state to file
def write_state(num):
    try:
        f = open(PATH + STATE, 'w')
    except:
        f = open(PATH + STATE, 'a')
    f.write(str(num))
    f.close()

def log(msg):
    
    f = open(HOME + 'logs.txt', 'a')

    # get current time
    now = datetime.datetime.now()
    f.write(now.strftime('[%Y-%m-%d %H:%M:%S] '))
    f.write(msg + '\n')
    f.close()

    
