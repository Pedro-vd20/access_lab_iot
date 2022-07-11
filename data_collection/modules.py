import os
import datetime

# shared code for multiple files

##########
# Constants
##########

HOME = '/home/pi/'

##########
# Code
##########

# makes running console commands easier
def run(arg):
    os.system(arg)

def log(msg):
    
    f = open(HOME + 'logs.txt', 'a')

    # get current time
    now = datetime.datetime.now()
    f.write(now.strftime('[%Y-%m-%d %H:%M:%S] '))
    f.write(msg + '\n')
    f.close()

    
