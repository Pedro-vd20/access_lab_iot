'''
ACCESS Lab, hereby disclaims all copyright interest in the program “ACCESS IOT 
Stations” (which collects air and climate data) written by Francesco Paparella, 
Pedro Velasquez.

Copyright (C) 2022 Francesco Paparella, Pedro Velasquez

This file is part of "ACCESS IOT Stations".

"ACCESS IOT Stations" is free software: you can redistribute it and/or modify it under the 
terms of the GNU General Public License as published by the Free Software 
Foundation, either version 3 of the License, or (at your option) any later 
version.

"ACCESS IOT Stations" is distributed in the hope that it will be useful, but WITHOUT ANY 
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR 
A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with 
"ACCESS IOT Stations". If not, see <https://www.gnu.org/licenses/>.

'''


import serial
import pigpio
import time
import pynmea2
from pynmea2.nmea import ChecksumError, ParseError
from datetime import datetime
from adafruit_bme280 import advanced as adafruit_bme280 #pip3 install adafruit-circuitpython-bme280
import adafruit_ms8607   #pip3 install adafruit-circuitpython-ms8607
import board
import busio

# ----- Imports for the sps30 dust sensor. -----
#download from: https://github.com/dvsu/sps30 (MIT license) and unpack
#in 'sps30_for_ACCESS', must be a subfolder of the folder containing
#'ACCESS_station_lib.py'.
try:
    import sys
    sys.path.append('/home/pi/sps30_for_ACCESS')
    from sps30_for_ACCESS.sps30 import SPS30
except ModuleNotFoundError:
    print("SPS30 library not found: you won't be able to use the sps30 dust sensor.")
# ----- end imports for the sps30 dust sensor. -----

#------------------------------------------------------
class GPSbeseecher:
    def __init__(self,
                 port = '/dev/ttySOFT0',
                 baudrate = 9600,
                 parity = serial.PARITY_NONE,
                 stopbits = serial.STOPBITS_ONE,
                 bytesize = serial.EIGHTBITS,
                 timeout = 0.5
                 ):
        self.serialprms = {
            'port':     port,
            'parity':   parity,
            'baudrate': baudrate,
            'stopbits': stopbits,
            'bytesize': bytesize,
            'timeout':  timeout,
        }

    def fix(self, timeout = 10):
        if type(timeout) not in (int, float):
            timeout = 10
        if timeout < 1:
            timeout = 10
        gpsfix = {
            'date': None,
            'time': None,
            'latitude': None,
            'lat_dir': None,
            'longitude': None,
            'lon_dir': None,
            'altitude': None,
            'alt_unit': None,
            'num_sats': None,
            'PDOP': None,
            'HDOP': None,
            'VDOP': None,
        }
        with serial.Serial(**self.serialprms) as ser:
            GGA_done = False
            RMC_done = False
            GSA_done = False
            start = time.time()
            while time.time() - start < timeout:
                #At startup readline may get a chopped, undecodable nmea string
                #Decoded strings may still contain gibberish: must catch
                #checksum and parse errors, too.
                try:
                    newdata = ser.readline().decode('ascii')
                    q = pynmea2.parse(newdata)
                except (UnicodeDecodeError, ChecksumError, ParseError):
                    continue #Just ignore invalid data and keep trying
                if q.sentence_type == 'GGA':
                    if q.gps_qual is None:
                        continue
                    if q.gps_qual > 0:
                        gpsfix['time']      = q.timestamp.isoformat()
                        gpsfix['latitude']  = q.latitude
                        gpsfix['longitude'] = q.longitude
                        gpsfix['lat_dir']   = q.lat_dir
                        gpsfix['lon_dir']   = q.lon_dir
                        gpsfix['altitude']  = q.altitude
                        gpsfix['alt_unit']  = q.altitude_units
                        gpsfix['num_sats']  = int(q.num_sats)
                        GGA_done = True
                if q.sentence_type == 'RMC':
                    if hasattr(q.datestamp, 'isoformat'):
                        gpsfix['date'] = q.datestamp.isoformat()
                        RMC_done = True
                if q.sentence_type == 'GSA':
                    gpsfix['PDOP'] = float(q.pdop)
                    gpsfix['HDOP'] = float(q.hdop)
                    gpsfix['VDOP'] = float(q.vdop)
                    GSA_done = True
                if GGA_done and RMC_done and GSA_done:
                    break
            #If GPS doesn't work, just set the time using the computer's clock.
            if gpsfix['time'] is None:
                CPUdate, CPUtime = datetime.utcnow().isoformat().split('T')
                gpsfix['time'] = CPUtime.split('.')[0]
                gpsfix['date'] = CPUdate
            return gpsfix

#--------------------------------------
#recall to install the daemon with 'sudo systemctl start pigpiod'
#pigpio's software serial does not have explicit parity and stop bits
class GPSbeseecherGPIO:
    def __init__(self,
                 RX_pin = 27,
                 baudrate = 9600,
                 bytesize = 8,
                 ):
        self.RX_pin = int(RX_pin)
        self.baudrate = int(baudrate)
        self.bytesize = int(bytesize)
        self.gpio = pigpio.pi()
        self.gpio.set_mode(RX_pin, pigpio.INPUT)

    def fix(self, timeout = 15):
        if type(timeout) not in (int, float):
            timeout = 15
        if timeout < 1:
            timeout = 15
        gpsfix = {
            'date': None,
            'time': None,
            'latitude': None,
            'lat_dir': None,
            'longitude': None,
            'lon_dir': None,
            'altitude': None,
            'alt_unit': None,
            'num_sats': None,
            'PDOP': None,
            'HDOP': None,
            'VDOP': None,
        }
        self.gpio.bb_serial_read_open(self.RX_pin, self.baudrate, self.bytesize)
        GGA_done = False
        RMC_done = False
        GSA_done = False
        time.sleep(3) #fill the buffer
        start = time.time()
        while time.time() - start < timeout:
            count, data = self.gpio.bb_serial_read(self.RX_pin)
            datalines = data.split()
            #
            #for l in datalines:
            #    print(l)
            #print()
            #
            for line in datalines:
                try:
                    newdata = line.decode('ascii')
                    q = pynmea2.parse(newdata)
                except (UnicodeDecodeError, ChecksumError, ParseError):
                    continue #Just ignore invalid data and keep trying
                try:
                    if q.sentence_type == 'GGA':
                        if q.gps_qual is not None and q.gps_qual > 0:
                            gpsfix['time']      = q.timestamp.isoformat()
                            gpsfix['latitude']  = q.latitude
                            gpsfix['longitude'] = q.longitude
                            gpsfix['lat_dir']   = q.lat_dir
                            gpsfix['lon_dir']   = q.lon_dir
                            gpsfix['altitude']  = q.altitude
                            gpsfix['alt_unit']  = q.altitude_units
                            gpsfix['num_sats']  = int(q.num_sats)
                            GGA_done = True
                    if q.sentence_type == 'RMC':
                        if hasattr(q.datestamp, 'isoformat'):
                            gpsfix['date'] = q.datestamp.isoformat()
                            RMC_done = True
                    if q.sentence_type == 'GSA':
                        gpsfix['PDOP'] = float(q.pdop)
                        gpsfix['HDOP'] = float(q.hdop)
                        gpsfix['VDOP'] = float(q.vdop)
                        GSA_done = True
                except Exception as e:
                    print(q)
                    print(e)
                    continue
                if GGA_done and RMC_done and GSA_done:
                    break
            if GGA_done and RMC_done and GSA_done:
                break
            else:
                time.sleep(3) #re-fill the buffer
        self.gpio.bb_serial_read_close(self.RX_pin)
        #If GPS doesn't work, just set the time using the computer's clock.
        if gpsfix['time'] is None:
            CPUdate, CPUtime = datetime.utcnow().isoformat().split('T')
            gpsfix['time'] = CPUtime.split('.')[0]
            gpsfix['date'] = CPUdate
        if gpsfix['date'] is None:
            CPUdate, CPUtime = datetime.utcnow().isoformat().split('T')
            gpsfix['date'] = CPUdate
        return gpsfix


#--------------------------------------

class NEXTPMbeseecher:
    """Instantiate an object of this class by specifying the serial port
    device. E.g.:

    pm = NEXTPMbeseecher(port=/dev/ttyAMA0)

    Baudrate, parity, etc. may also be specified, but they default to the
    values required by the Next-PM sensor. Any change should be unnecessary.

    High-level usage:

    pm.powerON()  - switches on fan and laser (no effect if already on)
    pm.powerOFF() - switches off fan and laser (no effect if already off)
    pm.is_ON()    - returns True (laser&fan are on) or False (they are off)
    pm.measurePM_10_seconds() - measures PM1, PM2.5, PM10 averaging over 10 s
    pm.measurePM_1_minute()   - measures PM1, PM2.5, PM10 averaging over 1 m
    pm.measurePM_15_minutes() - measures PM1, PM2.5, PM10 averaging over 15 m
    pm.measure() - starts up measurements (using measure_PM_1_minute) but additionally controls ON / OFF depending on humidity 
    pm.get_firmware_version() - returns a hex number in a 4-character string

    Note that the measurement methods are blocking, for a time
    comparable or longer than the nominal averaging time, determined
    by 'acquisition_time' parameter (in sec.) in the call of the
    '.measurePM_XXX' methods. Hoewever, if the sensor has been powered
    on for longer than the averaging time, the data may already be
    present in the sensor's memory and the reply would be much faster.

    Upon instantiation the on/off state of the hardware is not
    changed. However, the measurement methods will take about the nominal
    averaging time to reply if called immediately after initialization
    because the hardware doesn't keep track of how long it has been on,
    thus the object's software timer is set upon initialization.

    If the sensor is powered off, calling a measurePM method powers the sensor on.

    The sensor is rated for ~10000h (~1year) of fan and laser
    operation. Keeping it off if not necessary should increase its usable
    life span.

    Low-level usage:

       pm._send_cmd_get_rply(pm.NextPMcmd['Get_status'])

    This returns a byte string. Refer to the documentation (NextPM User
    Guide v.3.4) on p.6 and following for details on the meaning of the
    commands and how to interpret the result.

    """
    NextPMcmd = {
        'Get_PM_10sec':         b'\x81\x11\x6E',
        'Get_PM_60sec':         b'\x81\x12\x6D',
        'Get_PM_900sec':        b'\x81\x13\x6C',
        'Get_T_RH':             b'\x81\x14\x6B',
        'Toggle_PWR':           b'\x81\x15\x6A',
        'Get_status':           b'\x81\x16\x69',
        'Get_firmware_version': b'\x81\x17\x68',
    }
    SLEEP_BIT     = 1
    DEGRADED_BIT  = 2
    NOTREADY_BIT  = 4
    RH_ERROR_BIT   = 8
    TRH_ERROR_BIT = 16
    FAN_ERROR_BIT = 32
    MEM_ERROR_BIT = 64
    LAS_ERROR_BIT = 128
    #INVALID_ANSW is b'\x16' which shouln'd be returned by any of 
    #the first 4 commands when the sensor is switched on.
    INVALID_ANSW  = 22 

    # information for data_collection and error collection
    SENSOR = 'particulate_matter'
    TYPE = 'nextpm'
    
    def __init__(self,
                 port = '/dev/ttyAMA0',
                 baudrate = 115200,
                 parity = serial.PARITY_EVEN,
                 stopbits = serial.STOPBITS_ONE,
                 bytesize = serial.EIGHTBITS,
                 timeout = 1.0
                 ):
        self.port = port
        self.serialprms = {
            'port':     port,
            'baudrate': baudrate,
            'parity':   parity,
            'stopbits': stopbits,
            'bytesize': bytesize,
            'timeout':  timeout,
        }

        self._test_uart()

        #Make sure that the on/off status of the object reflects that
        #of the hardware. The following doesn't change the
        #sensor's actual on/off status
        if self._get_status()[2] & self.SLEEP_BIT == 1:
            self.powerOFF()
        else:
            self.powerON()

    def _checksum(self, bstring):
        if not isinstance(bstring, bytes):
            raise TypeError("'bstring' must be of type 'bytes'")
        return (256 - sum([x for x in bstring]) % 256 ) % 256
    
    def _send_cmd_get_rply(self, cmd):
        sleep_time = 0.5
        N_attempts = 3
        for i in range(N_attempts):
            if not isinstance(cmd, bytes):
                raise TypeError("'cmd' must be of type 'bytes'")
            with serial.Serial(**self.serialprms) as ser:
                ser.write(cmd)
                time.sleep(sleep_time)
                rply = ser.read_all()
                if rply == b'':
                    time.sleep(sleep_time*(i+1))
                    continue
            if self._checksum(rply[:-1]) == rply[-1]:
                break
            time.sleep(sleep_time*(i+1))
        else:
            raise ValueError(f"""
                NextPM on port {self.port} replied an empty string or failed the checksum. 
                Last reply after {N_attempts} was:
                {rply}
            """)
        return rply

    # attempt to read connection of serial ports
    def _test_uart(self):
        try:
            with serial.Serial(**self.serialprms) as ser:
                _ = ser.read_all()
                return True
        except Exception as err:
            print('Please check your serial connections. The port given could not be accessed.')
            print('It could be that your ttyS0 and ttyAMA0 configuration is flipped')
            raise(err)

    def _get_status(self):
        return self._send_cmd_get_rply(self.NextPMcmd['Get_status'])
    
    def powerON(self):
        """Switches on the sensor's fan and laser. If the sensor is already on only resets 'self.time_of_powerON' """
        if self._get_status()[2] & self.SLEEP_BIT == 1:
            self._send_cmd_get_rply(self.NextPMcmd['Toggle_PWR'])
        self.time_of_powerON = time.time()
        
    def powerOFF(self):
        """Switches off the sensor's fan and laser. If the sensor is already on only resets 'self.time_of_powerON' """
        if self._get_status()[2] & self.SLEEP_BIT == 0:
            self._send_cmd_get_rply(self.NextPMcmd['Toggle_PWR'])
        self.time_of_powerON = None

    def is_ON(self):
        """Returns False if the sensor is off, True otherwise. This
        interrogates the sensor's hardware, and resets the state of the
        NEXTPMbeseecher instance's internal timer if necessary"""
        if self._get_status()[2] & self.SLEEP_BIT == 1:
            #The following 'if' is unnecessary if there's only 1 object
            #of this class. With multiple object (maybe in different
            #processes) the status recorded in self.time_of_powerON
            #may not reflect the status of the hardware (given by
            #self._get_status())
            if self.time_of_powerON is not None:
                self.time_of_powerON = None
            return False
        else:
            if self.time_of_powerON is None:
                self.time_of_powerON = time.time()
            return True             
        #-----------
        #if self.time_of_powerON is None:
        #    return False
        #else:
        #    return True

    def _measurePM(self, cmd, acquisition_time):
        if not self.is_ON():
            self.powerON()
        time_elapsed_ON = time.time() - self.time_of_powerON
        if time_elapsed_ON < acquisition_time:
            time.sleep(acquisition_time - time_elapsed_ON)
        #Acquires sensor's Temperature and RH
        res = self._send_cmd_get_rply(self.NextPMcmd['Get_T_RH'])
        if (res[1] == self.INVALID_ANSW) or (res[2] & self.SLEEP_BIT == 1):
            raise ValueError(f"""
                    Invalid answer while requesting T and RH:
                    {res}
            """)
        T  = 0.9754*int.from_bytes(res[3:5], 'big')/100 - 4.2488
        RH = 1.1768*int.from_bytes(res[5:7], 'big')/100 - 4.7270
        #Acquires dust concentrations
        res = self._send_cmd_get_rply(cmd)
        if (res[1] == self.INVALID_ANSW) or (res[2] & self.SLEEP_BIT == 1):
            raise ValueError(f"""
                    Invalid answer while requesting PM:
                    {res} 
            """)
        return {
            "type": self.TYPE,
            "sensor": self.SENSOR,
            'PM1count':   int.from_bytes(res[3:5], 'big'),
            'PM2.5count': int.from_bytes(res[5:7], 'big'),
            'PM10count':  int.from_bytes(res[7:9], 'big'),
            'PM1mass':    round(0.1*int.from_bytes(res[9:11], 'big'), 1),
            'PM2.5mass':  round(0.1*int.from_bytes(res[11:13], 'big'), 1),
            'PM10mass':   round(0.1*int.from_bytes(res[13:15], 'big'), 1),
            'sensor_T':   round(T, 2),
            'sensor_RH':  round(RH, 2),
            'diagnostics': {
                'Degraded':   res[2] & self.DEGRADED_BIT != 0,
                'Notready':   res[2] & self.NOTREADY_BIT != 0,
                'Eccess_RH':  res[2] & self.RH_ERROR_BIT != 0,
                'T_RH_off':   res[2] & self.TRH_ERROR_BIT != 0,
                'Fan_error':  res[2] & self.FAN_ERROR_BIT != 0,
                'Mem_error':  res[2] & self.MEM_ERROR_BIT != 0,
                'Las_error':  res[2] & self.LAS_ERROR_BIT != 0,
            }
        }
        
    def measurePM_10_seconds(self, acquisition_time=30):
        return self._measurePM(self.NextPMcmd['Get_PM_10sec'],
                               acquisition_time)
    
    def measurePM_1_minute(self, acquisition_time=120):
        return self._measurePM(self.NextPMcmd['Get_PM_60sec'],
                               acquisition_time)

    #default measurement method is 1 minute.
    def measure(self):
        # turn on in case was off        
        self.powerON()

        data = self.measurePM_1_minute()

        # check humidity
        if data['sensor_RH'] < 55.0:
            self.powerOFF()

        return data

        
    def measurePM_15_minutes(self, acquisition_time=1000):
        return self._measurePM(self.NextPMcmd['Get_PM_900sec'],
                               acquisition_time)

    def get_firmware_version(self):
        res = self._send_cmd_get_rply(self.NextPMcmd['Get_firmware_version'])
        if res[1] == self.INVALID_ANSW:
            return "Power on the sensor to get the firmware answer"
        else:
            return bytes.hex(res[3:5])

# wrapper class to manage the bme 280 temperature, pressure and humidity sensor
# handles setting mode, setting overscanning
class BME280beseecher:

    MODES = (0x00, 0x01, 0x03)
    OVERSCANS = (0x00, 0x01, 0x02, 0x03, 0x04, 0x05)

    SENSOR = 'air_sensor'
    TYPE = 'bme280'
    

    # i2c -> board.I2C() for the raspberry pi
    # mode -> run in sleep (0x00), force (0x01), or normal (0x03) mode, Default
    #   is force mode
    # overscan -> oversampling setting for each of the measurements. Only valid \
    #   values: 1, 2, 4, 8, 16
    #   Default is 16
    def __init__(self, 
                 i2c: busio.I2C = None, 
                 mode: int = 0x01, 
                 overscan: int = 0x05
                ):
        
        if i2c == None:
            i2c = board.I2C()

        self.i2c = i2c
        self.sensor = adafruit_bme280.Adafruit_BME280_I2C(i2c)

        # set mode to force
        if mode not in self.MODES:
            mode = 0x01
            print('Mode not allowed, defaulting to 0x01, force mode')
        self.sensor.mode = mode

        # set overscan
        if overscan not in self.OVERSCANS:
            overscan = 0x05
            print('overscan not allowed, defaulting to 16')
        self.sensor.overscan_humidity = overscan
        self.sensor.overscan_temperature = overscan
        self.sensor.overscan_pressure = overscan
        # ERROR: DO ERROR CHECKING HERE!!! WHAT COULD GO WRONG????


    # measure pressure, humidity, and temperature
    # return json dict with the values
    def measure(self) -> dict:
        # ERROR: what happens if mode is sleep????
        hum = self.sensor.humidity
        temp = self.sensor.temperature
        prssr = self.sensor.pressure

        return {
            'type': self.TYPE,
            'sensor': self.SENSOR,
            'humidity': hum,
            'temperature': temp,
            'pressure': prssr
        }

    # return the mode the sensor is currently on
    def get_mode(self) -> int:
        return self.sensor.mode

    # set the mode of the sensor
    # possible modes are 
    #   0x00, sleep 
    #   0x01, force
    #   0x03, normal
    # returns False if illegal mode, True if successfully changed
    def set_mode(self, mode: int) -> bool:
        if mode not in self.MODES:
            print('Mode not allowed, only allowed:', self.MODES, sep='\n')
            return False
        self.sensor.mode = mode
        return True

    # get current level of oversampling performed
    # returns 3 integers for humidity, temperature, and pressure respectively
    def get_overscan(self) -> tuple:
        return self.sensor.overscan_humidity, self.sensor.overscan_temperature \
            , self.sensor.overscan_pressure

    # set the oversampling of all fields
    # possible values are 1 2 4 8 16
    # returns False if illegal overscan value, True if successfully changed
    def set_overscan(self, overscan: int) -> bool:
        if overscan not in self.OVERSCANS:
            print('Overscan setting not allowed. Only the following allowed:', self.OVERSCANS, sep='\n')
            return False
        self.sensor.overscan_humidity = overscan
        self.sensor.overscan_temperature = overscan
        self.sensor.overscan_pressure = overscan
        return True

    # set the oversampling of humidity only
    # possible values are 1 2 4 8 16
    # returns False if illegal overscan value, True if successfully changed
    def set_overscan_humidity(self, overscan: int) -> bool:
        if overscan not in self.OVERSCANS:
            print('Overscan setting not allowed. Only the following allowed:', self.OVERSCANS, sep='\n')
            return False
        self.sensor.overscan_humidity = overscan
        # self.sensor.overscan_temperature = overscan
        # self.sensor.overscan_pressure = overscan
        return True

    # set the oversampling of temperature only
    # possible values are 1 2 4 8 16
    # returns False if illegal overscan value, True if successfully changed
    def set_overscan_temperature(self, overscan: int) -> bool:
        if overscan not in self.OVERSCANS:
            print('Overscan setting not allowed. Only the following allowed:', self.OVERSCANS, sep='\n')
            return False
        # self.sensor.overscan_humidity = overscan
        self.sensor.overscan_temperature = overscan
        # self.sensor.overscan_pressure = overscan
        return True

    # set the oversampling of pressure only
    # possible values are 0, 1, 2, 3, 4, 5
    # returns False if illegal overscan value, True if successfully changed
    def set_overscan_pressure(self, overscan: int) -> bool:
        if overscan not in self.OVERSCANS:
            print('Overscan setting not allowed. Only the following allowed:', self.OVERSCANS, sep='\n')
            return False
        # self.sensor.overscan_humidity = overscan
        # self.sensor.overscan_temperature = overscan
        self.sensor.overscan_pressure = overscan
        return True

#-------------------------------------------------
# wrapper class for the humidity-temperature-pressure sensor ms8607
# requires the package adafruit-circuitpython-ms8607
class MS8607beseecher:

    SENSOR = 'air_sensor'
    TYPE = 'ms8607'

    # i2c -> board.I2C() for the raspberry pi
    def __init__(self, 
                 i2c: busio.I2C = None, 
                ):
        
        if i2c == None:
            i2c = board.I2C()

        self.i2c = i2c
        self.sensor = adafruit_ms8607.MS8607(i2c)

        # ERROR: DO ERROR CHECKING HERE!!! WHAT COULD GO WRONG????
        # WHAT ABOUT THE INITIALIZE METHOD I SAW
        # AND WHAT ABOUT CALIBRATION??


    # measure pressure, humidity, and temperature
    # return json dict with the values
    def measure(self) -> dict:
        hum = self.sensor.relative_humidity
        temp = self.sensor.temperature
        prssr = self.sensor.pressure

        return {
            'type': self.TYPE,
            'sensor': self.SENSOR,
            'humidity': hum,
            'temperature': temp,
            'pressure': prssr
        }

# Provides an error class that can be initiated when the script fails to 
# initialize any sensor
# Only goal is to keep a sensor object so diagnostics can encounter error and send information
class ErrorBeseecher:

    # Only stores an error message
    # @param type -> brand of sensor (i.e BME280, NEXTPM, etc)
    # @param sensor -> what this sensor measures (i.e air_sensor, particulate_matter)
        # this should reflect the 'sensor' field that would be returned had the 
        # beseecher initialized successfully
    def __init__(self, sensor, type, msg='Error at boot'):
        # message to display when exception is raised
        self.message = msg
        self.type = type
        self.sensor = sensor

    def measure(self): # only here to artificially raise an exception
        # return exception as dictionary
        raise(Exception(self.message))
#--------------------------------------
# Sensirion sps30 dust sensor.
class SPS30beseecher:
    """Wrapper around the 'SPS30' class (from https://github.com/dvsu/sps30).

Usage: 

sps = SPS30beseecher()
mydata = sps.measure()

At initialization the i2c bus number may be specified (defaults to 1);
an auto-cleaning interval may also be specified (defaults to 1 day).

    """
    #Translations from the sps30 class data dictionary keynames to our keynames.
    tr_mass  = {'pm1.0':  'PM1mass',
                'pm2.5':  'PM2.5mass',
                'pm4.0':  'PM4mass',
                'pm10': 'PM10mass',
                }
    tr_count = {'pm0.5':  'PM0.5count',
                'pm1.0':  'PM1count',
                'pm2.5':  'PM2.5count',
                'pm4.0':  'PM4count',
                'pm10': 'PM10count',}
    tr_diag =  {'fan_status':   'Fan_error',
                'speed_status': 'Spd_error',
                'laser_status': 'Las_error',
                }

    SENSOR = 'particulate_matter'
    TYPE = 'sps30'

    def __init__(self,
                 i2c_bus_number = 1,
                 cleaning_interval_in_days = 1
                 ):
        # The following raises a 'FileNotFoundError' exception if
        # the specified i2c bus does not exists.
        self.sps = SPS30(bus = i2c_bus_number)
        self.i2c_bus_number = i2c_bus_number 
        self.sps.write_auto_cleaning_interval_days(cleaning_interval_in_days)
        self.sps.start_measurement() #we keep the sps30 always on:
                                     #max power draw 80mA
                                     
    def measure(self):
        sensor_data = self.sps.get_measurement()['sensor_data']
        results = {'type': self.TYPE, 'sensor': self.SENSOR}
        for k in sensor_data['mass_density'].keys():
            results[self.tr_mass[k]] = sensor_data['mass_density'][k]
        for k in sensor_data['particle_count'].keys():
            results[self.tr_count[k]] = sensor_data['particle_count'][k]
        results['Typical_particle_size'] = sensor_data['particle_size']
        sensor_diagnostics = self.sps.read_status_register()
        diag = {}
        for k in sensor_diagnostics.keys():
            diag[self.tr_diag[k]] = False if sensor_diagnostics[k] == 'ok' \
                else True
        results['diagnostics'] = diag
        return results
