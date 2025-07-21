#
# Schlüsselkasten V2 Hardware SETUP
#


# version string
__version__ = "2.0.0-alpha1"

#get hardware info (on RPi)
platform = "Test PC"

nfc_serial = "COM1"

def reset():
    pass
    
class compartment():
    def __init__(self):
        self.door_status = "unknown"
        self.content_status = "unknown"
        
    def get_inputs(self):
        return False
    def open(self):
        return True

backlight = None
# set up diode on pin
supply_present = None

# set up acc interrupt pin
acc_int = None

# set up hapt interrupt pin
hapt_int = None


# set up lock interrupt pin
lock_int = None


# piezo buzzer
piezo = None

haptic = None
    

try:
    accelerometer = adafruit_lis3dh.LIS3DH_I2C(i2c_sys, address=0x19)
except Exception as e:
    accelerometer = None
    #TODO: logger.error(f"Error setting up accelerometer: {e}")

try:
    light_sensor = adafruit_veml7700.VEML7700(i2c_sys) # 0x10 read: light_sensor.lux
except Exception as e:
    light_sensor = None
    #TODO: logger.error(f"Error setting up brightness sensor: {e}")

try: 
    # TODO: add support for the BQ34210
    battery_monitor = None
except Exception:
    battery_monitor = None
    #TODO: logger.error(f"Error setting up battery monitor: {e}")

# get connected port expanders on two buses (adresses from 0x20 to 0x27, prototype PCBs: 0x24 to 0x27)
# first bus/connector        
port_expanders = []


compartments = {}
        
# initializes the port expanders and compartmnts
def init_port_expanders(large_compartments):
    for x in range (1,21):
        compartments[str(x)] = compartment()
        
