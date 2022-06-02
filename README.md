# Access Lab IOT Assistantship

This guide assumes the operating system is Linux, the sender is running off a Raspberry Pi 4.

## INCLUDE OS VERSIONS FOR DEVICES

## Receiver

The receiver is a Flask server waiting for the various senders to authenticate themselves and send data collected in the form of `.csv`, `.txt`, or `.json` files.

### Related Files
* `ids.txt`: contains list of all PI ids for server to check.
* `receiver.py`, `temp_upload.py`: older versions of the receiver, non-functioning.
* `upload.py`: flask server to manage receiving files.
*`received_files/`: directory where flask server will save both sha256 checksums and data collected.


### Installing dependencies

The server must have python3 and pip3 installed and updated. To install the remaining dependencies, simply run the following.

```console
$ pip3 install Flask
$ pip3 install pyopenssl 
```

### Setting up

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

```
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

`cert.pem` and `key.pem` should be created following this. Whatever happens, never share `key.pem` or send it anywhere. In the [Sender](#setting-up-1) section, we will cover how to send the certificate to the PIs.

### Running the receiver

Make sure to change your current directory to the same as `upload.py`. Then simple run

```console
$ flask run --host=my_ip --port=3500 --cert=cert.pem --key=key.pem
```

For this project, the port to be used has been defined as 3500. This will always be the case. `my_ip` should be the public IP address of the server. This will run the project in development mode and is fine for now while testing occurs. Later, the project must be deployed as production version, as this one is more stable and secure.

### Possible errors
* `Error finding files and folders`: receiver could not find `ids.txt` or the folder `received_files/`. The server will not run. Please make sure `uplodad.py`, `received_files/`, and `ids.txt` are all in the same directory and that the server 
* `Unauthorized access, rejected`: receiver failed to find a valid pi_id in the request. The request is ignored.

The rest of the errors assume successful validation

* `Required files not included`: The request to send a file does not include the file or the checksum. File does not get downloaded, request is ignored.
* `Empty file or checksum fields`: the file and checksum are not missing but are left empty by the sender. Request gets ignored.
* `Wrong file type`: the sent file is of the wrong type. Request is ignored.
* `Wrong checksum`: the checksum sent does not match the sent file. The file is not downloaded and the request is ignored.

___

## Sender

The sender uses the Python requests module to securely send the data collected by the Pi to the main server.

### Related Files
* `sender.py`: script to send files to a remote server.
* `secret.py`: contains simply 1 line of code, storing the Pi's 16-digit hexadecimal id.
* `sent_files/`: directory where all the files are moved after they are successfully sent.

### Installing dependencies

The sender must have python3 and pip3 installed and updated. To install the remaining dependencies, simply run the following.

```console
$ pip3 install requests
```

### Setting up

Before running the sender, please make sure the following three files/directories must be in the same path:

1. `sender.py`
3. `secret.py`

When running the code, if the sender cannot find `sent_files/`, it will create it in the same directory as the directory of unsent files. The [next section](#running-the-sender) will further discuss this file structure.

The final step is installing the self-signed certificate created by the receiver. This will allow the sender to trust the identity of the server. Certificates in Raspberry Pis are stored in `/etc/ssl/certs`, and thus, the following command will send the certificate:

```console
$ scp user@server_ip:path_to_cert/cert.pem /etc/ssl/certs/
```

### Running the sender

Unlike receiver, the sender can be run from any path.

```console
$ python3 path_to_sender/sender.py arg1 arg2 
```

`arg1` is the ip address of the server.

`arg2` is the path where data is stored.

`arg2` can be absolute or relative from wherever `sender.py` will be called. If `arg2 = /home/pi/logs/` then `sent_files/` must be located at `/home/pi/sent_files`. If this directory does not exist, `sender.py` will create it.

### Possible errors

* `PI id not found`: the sender failed to import its own id. The script will stop running. Make sure the file `secret.py` is in the same directory as `sender.py` and has the following: `secret='pi_id'` where pi_id is a 16-digit hexadecimal string.
* `Missing arguments`: the sender did not get the required arguments. The script will stop running.
* `arg2 not a valid directory`: sender could not access the folder with the logs to send. The script will stop running.
* `http://arg1:3500 could not be reached`: sender could not reach flask receiver, the script stops running 
* `Authentication failed`: server was unable to verify Pi's identity, sender stops running
* `file_name could not be sent`: error verifying checksum of sent file. Sender will simply keep that file in the logs folder rather than moving it to the directory of sent files. The script will continue to run, sending other files. This unsent file will be sent the next time the script runs.
