from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def hello_world():
    sernum = request.args.get('station_serial_number')
    if sernum == 'xyz':
        return 'Giusto!'
    else:
        return str(sernum)+"|You shouldn't be here!"

# route to post new data on server
@app.route('/data', methods=['POST'])
def download_data():
    print(request.data)
    print()

    return "200"
    
if __name__ == "__main__":
    #app.run(ssl_context='adhoc')
    app.run()
