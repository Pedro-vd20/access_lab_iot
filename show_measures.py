from flask import Flask, request, render_template, redirect

##########

PATH = '/home/pi/' # later to be replaced with path to logs

##########

# return own NAT IP for Pi to host site
def get_ip():
    return '127.0.0.1'

# gets most recent measurement file
def get_file():
    return PATH + '2022-06-18T12:41:43Z.json'

##########

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    f_name = get_file()

    try:
        f = open(f_name, 'r')
    except:
        return 'No measurements yet' # to implement later

    return ''.join(f.readlines())


app.run(host=get_ip(), port=3500)
