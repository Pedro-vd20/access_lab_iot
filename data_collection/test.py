import ACCESS_station_lib as access
from sensors import *
from modules import log


# all this file will do is attempt to request measurements from all sensors
# if it crashes at any point, it will log failure and let the user know
def main():
    try:
        print('Testing Particle Measure Sensors')
        for i in range(len(pm)):
            print('Testing', i)
            print('Is on:', pm[i].is_ON())
        print()

        print('Testing Air Sensors')
        for i in range(len(air_sens)):
            print('Testing', i)
            print(air_sens[i].measureATM())
        print()

        print('Testing GPS')
        print(gps.fix())
        print()

    except Exception as e:
        print('Error connecting to sensors')
        log('Testing sensors failed, must check connection')
        raise(e)


if __name__ == '__main__':
    main()
