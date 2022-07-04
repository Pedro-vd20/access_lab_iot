# Access Lab Measurement Stations

This guide assumes the operating system is Linux, the sender is running off a Raspberry Pi 4.

## CHECKLIST

1. Error codes for sender/receiver DONE
2. Add email functionality CANCELLED
3. Add section with all dependencies for pi and local server
4. Better user-friendly messages while pi reboots / checks for errors
5. Change test-network in boot to contact receiver rather than google.com
6. Logging info with error codes?
7. Add hardware wiring section
8. Fix state 0 to install all other dependencies
9. Include images for hardware section
10. Fix related files to include Access files
11. Describe logging info (how to access them and all)
12. Diagnostic file (have Pi send out diagnostics like memory, temp etc once a day)
13. Complete wrapper class bme280 beseecher and ms8607 beseecher
14. Change print to log in sender / receiver
15. Create folder structure for sender once all files are accounted for.
16. Create access email for this
17. Change sender section to Access station section
18. Basically rewrite whole Access Station section
19. Detal OS specifications and dependency versions
20. List the different sites the receiver hosts (upload, home page, etc)
21. Add files that the boot creates for temp purposes
22. Is it possible for pi not to reboot after all the changes and stuff??? would greatly speed up
1. Add whole section on setting up ports and stuff
1. Test script for sensors
1. Add server website to see station

## Receiver

The receiver is a Flask server waiting for the various Access Stations to authenticate themselves and send data collected in the form of `.csv`, `.txt`, or `.json` files. It also receives diagnostics from the stations. Additionally, it allows users to see the data collected by the station they're hosting.

### Related Files
* `ids.csv`: contains list of all PI ids and their registered email for server to check.
* `receiver.py`, `temp_upload.py`: older versions of the receiver, non-functioning.
* `upload.py`: flask server to manage receiving files.
* `register.py`: generates new random id for brand new access stations. 
* `logs.txt`: if non-existant, `upload.py` will create it and write errors or important info on it.
* `received_files/`: directory where flask server will save both sha256 checksums and data collected.


### Installing dependencies

The server must have python3 and pip3 installed.

```console
$ sudo apt-get update
$ sudo apt-get upgrade
$ sudo apt-get install python3
$ sudo apt-get install python3-pip
```

#### Dependencies

* Flask 2.1.2
* werkzeug 2.1.2
* pyopenssl 
* os
* random
* string

#### Installation

```console
$ pip3 install Flask
$ pip3 install pyopenssl 
```

### Setting up

Before running the server, please make sure the following three files/directories must be in the same path:

```console
./
 |-- upload.py
 |-- ids.csv
 |-- register.py
 |-- logs.txt
 |-- received_files/
 |   |--
 |
```

The code uses relative paths so it's essential these files are in the same directory.

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
Organizational Unit Name (eg, section) []:Access
Common Name (e.g. server FQDN or YOUR name) []:ip_addr
Email Address []:
```

`ip_addr` must be the server's ip address.

`cert.pem` and `key.pem` should be created following this. Never share `key.pem`. In the [Sender](#setting-up-1) section, we will cover how to send the certificate to the Access Stations. This new certificate-key pair should last for about 10 years (3652 days). Typically a shorter expiry is recommended, but for testing and for this lab, 10 years will be chosen. The current certificates will expire on May 2032 and must be replaced in all stations.

### Running the receiver

Make sure to change your current directory to the same as `upload.py`. 

```console
./
 |-- upload.py
 |-- ids.csv
 |-- register.py
 |-- cert.pem
 |-- key.pem
 |-- logs.txt
 |-- received_files/
 |   |--
 |
````

Then run:

```console
$ flask run --host=my_ip --port=3500 --cert=cert.pem --key=key.pem
```

For this project, the port to be used has been defined as 3500. This will always be the case. `my_ip` should be the public IP address of the server. This will run the project in development mode and is fine for now while testing occurs. Later, the project must be deployed as production version, as this one is more stable and secure.

### Possible errors

The following errors will be logged into the receiver's log files.

* `Error finding files and folders`: receiver could not find `ids.csv` or the folder `received_files/`. The server will not run. Please make sure `uplodad.py`, `received_files/`, and `ids.txt` are all in the same directory and that the server 
* `Unauthorized access, rejected`: receiver failed to find a valid pi_id in the request. The request is ignored.

The rest of the errors assume successful validation

* `Required files not included`: The request to send a file does not include the file or the checksum. File does not get downloaded, request is ignored.
* `Empty file or checksum fields`: the file and checksum are not missing but are left empty by the sender. Request gets ignored.
* `Wrong file type`: the sent file is of the wrong type. Request is ignored.
* `Wrong checksum`: the checksum sent does not match the sent file. The file is not downloaded and the request is ignored.

### Response Codes

The receiver will respond with any of the following response codes:

* `200`: request successful, files received and verified.
* `301 new_url`: the request was received successfully and the file should be sent to `/upload/new_url`.
* `401`: unathorized request. The server will ignore the request.
* `412`: precondition failed, files to receive not sent in request.
* `415`: unsopported file type received, request rejected.
* `500`: error receiving file, checksum could not be verified.

___

## Access Stations

The Access Stations have two main modes: boot and data collection.

### Setting Up

This guide will follow the steps from boot up to operation required to set up the Access Station.

1. Booting the RPi: configure the keyboard and and username. The user for all stations should be `pi`. 

1. Configure the settings:

    ```console
    $ sudo raspi-config
    ```
    1. Enable `Interface Options`->`SSH`
    1. Enable `Interface Options`->`I2C`
    1. In `Interface Options`->`Serial Port` disable login shell but enable serial port hardware.
    1. Configure `Localisation Options`->`WLAN Country`
    1. Enable 

1. Connect to the network.
    ```console
    $ sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
    ```
    and add the following at the end of the file:

    ```console
    network={
        ssid="nyu"
        proto=RSN
        key_mgmt=WPA-EAP
        eap=PEAP
        identity="net_id"
        password="password"
        phase2="auth=MSCHAPV2"
        priority=1
    }
    ```

    replacing `net_id` and `password` with your own.    

    Then reboot the RPi to connect and implement the settings from step (2).

1. Download the necessary files and setup the folder structure as described [here](#folder-structure)

1. Make sure Python3 and pip3 are properly installed.

    ```console
    $ sudo apt update
    $ sudo apt upgrade -y
    $ sudo apt-get install python3-pip -y
    ```

1. Run `dependencies.py` to install all dependencies.

    ```console
    $ python3 /home/pi/boot/dependencies.py
    ```

1. Configue serial ports, making sure the `ttyS0` is not set as `serial0`.

    ```console
    $ sudo nano /boot/config.txt
    ```

    Add the following at the bottom of the file.

    ```console
    dtoverlay=miniuart-bt
    dtoverlay=uart2
    ```

    Make sure both serial ports are properly set by running

    ```console
    $ ls -l /dev
    ```
    
    `serial0` should be mapped to `ttyAMA0` and `ttyAMA1` should also appear on the outputs.

1. Connect the RPi to the sensors
    
    WHAT DEVICES GO WHERE LIST PINS HERE

1. Run `test.py` to do a quick test of all the hardware. If the RPi reboots, the hardware testing was successful.

1. Wait to see if it becomes a wireless access station. If the `access` network becomes visible, the station has been successfully set up.
___

The Access Stations have two main modes: boot and data collection.

### Folder Structure

```console
/home/pi/
 |-- boot/
 |   |-- app.py
 |   |-- dependencies.py
 |   |-- modules.py
 |   |-- setup.py
 |   |-- state.txt
 |   |-- services/
 |   |   |-- flask_app.service
 |   |   |-- setup.service 
 |   |-- static/
 |   |   |-- app.js
 |   |   |-- styles.css
 |   |   |-- images/
 |   |   |   |-- ACCESS_LOGO_SQUARE_violet_drop1.png
 |   |-- templates/
 |   |   |-- index.html
 |   |   |-- no_networks.html
 |   |   |-- testing_wifi.html
 |-- ACCESS_station_lib.py
 |-- data_collection.py
 |-- sender.py
 |-- station_id.py
 |-- test.py
 |
```

### Installing Dependencies

The Access Station must have python3 and pip3 installed.

```console
$ sudo apt-get update
$ sudo apt-get upgrade
$ sudo apt-get install python3
$ sudo apt-get install python3-pip
```

#### Dependencies

Python dependencies
* Flask 2.1.2
* requests 2.25.1
* pyserial 3.5
* pigpio 
* pynmea
* adafruit_bme280
* adafruit_ms8607

Other dependencies
* hostapd 2:2.9.0-21
* dnsmasq 2.85-1
* pigpiod 1.79-1+rpt1



### Boot Mode

The first mode of the Access Station is boot mode. Here the station goes through the installation of required dependencies, settings configuration, and connection to wifi once deployed in a new location.

#### Related Files

All files inside the boot folder will setup the Access Station.

* `app.py`: small flask server whos only purpose is to collect the wifi information from the user in order to connect.
* `modules.py`: shared code and constants imported by other python files.
* `setup.py`: main driver for setting up the access stations. Checks the current state of the machine and continues with next steps by running other files / executing commands.
* `state.txt`: stores the current state of the station. If the file is non-existant, the state is assumed as 0. States can range from 0 to 5.
* `services/`: system services to automatically run the setup and the flask app each time the station boots.
* `static/`: resources for the flask app such as images, stylesheets, and javascript code.
* `templates/`: html pages for the flask app to render.



The boot process will use various other files for quick storage of network status and information.

#### States




The sender uses the Python requests module to securely send the data collected by the Pi to the main server.

### Related Files
* `sender.py`: script to send files to a remote server.
* `secret.py`: contains simply 1 line of code, storing the Pi's 16-digit hexadecimal id.
* `sent_files/`: directory where all the files are moved after they are successfully sent.

### Installing dependencies

The sender must have python3 and pip3 installed and updated.

#### Dependencies
* requests
* Flask
* hostapd
* dnsmasq
* pigpiod
* serial
* pigpio
* pynmea2
* adafruit_bme280
* adafruit_ms8607
* google
* google-auth
* google-api-python-client

___

* google-auth-httplib2
* google-auth-oauthlib

```console
$ pip3 install requests
$ pip3 install google-auth
$ pip3 install google-api-python-client
$ pip3 install google-auth-httplib2
$ pip3 install google-auth-oauthlib
$ sudo apt-get -y pigpiod
```

### Setting up

Before running the sender, please make sure the following three files/directories must be in the same path:

1. `sender.py`
3. `secret.py`

When running the code, if the sender cannot find `sent_files/`, it will create it in the same directory as the directory of unsent files. The [next section](#running-the-sender) will further discuss this file structure.

The final step is installing the self-signed certificate created by the receiver. This will allow the sender to trust the identity of the server. The certificate can be installed anywhere, but for ease, should be placed in the same directory as `sender.py`.

```console
$ scp user@server_ip:path_to_cert/cert.pem path_to_store_certificate/
$ export REQUESTS_CA_BUNDLE=/absolute_path_to_certificate/cert.pem
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
* `https://arg1:3500 could not be reached`: sender could not reach flask receiver, the script stops running 
* `Authentication failed`: server was unable to verify Pi's identity, sender stops running
* `file_name could not be sent`: error verifying checksum of sent file. Sender will simply keep that file in the logs folder rather than moving it to the directory of sent files. The script will continue to run, sending other files. This unsent file will be sent the next time the script runs.
