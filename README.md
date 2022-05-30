# Access Lab IOT Assistantship

## Related files and directories
### Receiver
* `ids.txt`: contains list of all PI ids for server to check.
* `receiver.py`, `upload_temp.py`: older versions of the receiver, non-functioning.
* `upload.py`: flask server to manage receiving files.
*`received_files/`: directory where flask server will save both sha256 checksums and data collected.

### Sender
* `sender.py`: script to send files to server from pi
* `secret.py`: contains simply 1 line, meant to store individual Pi's id.
* `sent_files/`: directory where all files sent successfully will be moved to.

## Dependencies

Python dependencies:
* os
* hashlib
* Flask
* werkzeug
* random
* string


## Server (receiver)
### Installing Flask
For a quick guide on installing Flask, you may refer to the following [guide](https://phoenixnap.com/kb/install-flask).

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
