# Access Lab IOT Assistantship

This guide assumes the operating system is Linux, the sender is running off a Raspberry Pi 4.

## INCLUDE OS VERSIONS FOR DEVICES

## Receiver

### Related Files
* `ids.txt`: contains list of all PI ids for server to check.
* `receiver.py`, `upload_temp.py`: older versions of the receiver, non-functioning.
* `upload.py`: flask server to manage receiving files.
*`received_files/`: directory where flask server will save both sha256 checksums and data collected.


### Installing dependencies

The server must have python3 and pip3 installed and updated. To install the remaining dependencies, simply run the following.

```console
$ pip3 install Flask
$ pip3 install pyopenssl 
```

### Setting up the workspace

Before running the server, please make sure the following three files/directories must be in the same path:

1. `upload.py`
2. `received_files/`
3. `ids.txt`

The code uses relative paths so it's essential these 3 are in the same directory.

For Flask to run, you must set up the `FLASK_APP` environment variable.

```console
$ export FLASK_APP=upload.py
```

It is also possible to use `upload.py`'s absolute path, though this is not necessary as the Flask app is expected to be run from the same directory.

Next step is to generate a self-signed certificate for the server to use. Using pyopenssl, we can create both a certificate and private key using the following:

```console
$ openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 3652 
```

Running the line above will lead to the following prompts to fill in:

```console
Generating a RSA private key
....++++
.........................................................................................................................................++++
writing new private key to 'key.pem'
-----
You are about to be asked to enter information that will be incorporated
into your certificate request.
What you are about to enter is what is called a Distinguished Name or a DN.
There are quite a few fields but you can leave some blank
For some fields there will be a default value,
If you enter '.', the field will be left blank.
-----
Country Name (2 letter code) [AU]:AE
State or Province Name (full name) [Some-State]:Abu Dhabi
Locality Name (eg, city) []:Abu Dhabi
Organization Name (eg, company) [Internet Widgits Pty Ltd]:Access
Organizational Unit Name (eg, section) []:
Common Name (e.g. server FQDN or YOUR name) []:
Email Address []:

```

___


## Related files and directories
### Sender
* `sender.py`: script to send files to server from pi
* `secret.py`: contains simply 1 line, meant to store individual Pi's id.
* `sent_files/`: directory where all files sent successfully will be moved to.

## Dependencies

Python dependencies:
* os
* hashlib

### Receiver Only
* pyopenssl
* Flask
* werkzeug
* random
* string


## Server (receiver)
### Installing Flask
For a quick guide on installing Flask, you may refer to the following [guide](https://phoenixnap.com/kb/install-flask).

### Setting up certificates
Run `$ pip3 install pyopenssl` 

To create a new certificate:

`$ openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 3652`

cert.pem is the certificate and key.pem the private key.

The pis store their certificates in `/etc/ssl/certs`, and a copy of cert.pem must be sent there.

To copy from machines: `scp user@server:/absolute_location_of_cert pi@pi_ip:/absolute_dest`

### Setting up
To set up flask, navigate to the receiver folder and move the `upload.py` file to your desired directory. Then, run `export FLASK_APP=/current_path/upload.py`.

Before running, be sure to move `ids.txt` and `received_files/` folder to the same directory as `upload.py`.

### Running receiver
To run, first, cd to the directory where `upload.py` can be found. The app requires relative paths so it's imperative to run from the same directory. Then simply type `flask run --host=your_device_ip --port=3500`. This will launch the code in debug mode, but hosted on your local network. Port 3500 has been chosen for this project, the server will always run on this port.

### Possible errors
* `Error finding files and folders`: receiver could not find `ids.txt` or the folder `received_files/`. The server will not run. Please make sure `uplodad.py`, `received_files/`, and `ids.txt` are all in the same directory.

## Client (sender)
To run the client, simply run 

`python3 sender.py arg1 arg2` 

where `arg1` is the ip address of the server and `arg2` is the path to the folder where all the logs to send are stored. 

### Possible errors
*`PI id not found`: the sender failed to import its own id. The script will stop running. Make sure the file `secret.py` is in the same directory as `sender.py` and has the following: `secret='pi_id'` where pi_id is a 16-digit hexadecimal string.
* `Missing arguments`: the sender did not get the required arguments. The script will stop running.
* `arg2 not a valid directory`: sender could not access the folder with the logs to send. The script will stop running.
* `http://arg1:3500 could not be reached`: sender could not reach flask receiver, the script stops running 
* `Authentication failed`: server was unable to verify Pi's identity, sender stops running
* `file_name could not be sent`: error verifying checksum of sent file. Sender will simply keep that file in the logs folder rather than moving it to the directory of sent files. The script will continue to run, sending other files. This unsent file will be sent the next time the script runs.
