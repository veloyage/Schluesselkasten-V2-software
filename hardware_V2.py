#
# Schlüsselkasten V2 Hardware SETUP
#

import board
import pwmio
import digitalio
from adafruit_extended_bus import ExtendedI2C as I2C

from adafruit_mcp230xx.mcp23017 import MCP23017 # port expander
import adafruit_lis3dh # accelerometer
import adafruit_veml7700 # light sensor
import adafruit_drv2605 # haptic driver

import platform    # For getting the operating system name
import subprocess  # For executing a shell command

import compartment

from pi5neo import Pi5Neo as SPIneo

# version string
__version__ = "2.0.0-alpha1"
    
# 4 separate buses on V2
i2c_sys = I2C(4)  # Device is /dev/i2c-4
i2c_ext1 = I2C(1)  # Device is /dev/i2c-1
i2c_ext2 = I2C(5)  # Device is /dev/i2c-5
i2c_ee = I2C(0)  # Device is /dev/i2c-0


backlight = pwmio.PWMOut(board.D19, frequency=1000, duty_cycle=int(1 * 65535))
# set up diode on pin
supply_present = digitalio.DigitalInOut(board.D25)
supply_present.direction = digitalio.Direction.INPUT

# set up acc interrupt pin
acc_int = digitalio.DigitalInOut(board.D24)
acc_int.direction = digitalio.Direction.INPUT

# set up hapt interrupt pin
hapt_int = digitalio.DigitalInOut(board.D23)
hapt_int.direction = digitalio.Direction.OUTPUT
hapt_int.value = False

# set up lock interrupt pin
lock_int = digitalio.DigitalInOut(board.D22)
lock_int.direction = digitalio.Direction.INPUT

## LED config 
LED_connector_1 = SPIneo('/dev/spidev1.0', 30, 1000)
LED_connector_2 = SPIneo('/dev/spidev4.0', 30, 1000)
LED_connector_3 = SPIneo('/dev/spidev0.0', 3, 1000, "RGBW")

# piezo buzzer
piezo = pwmio.PWMOut(board.D18, frequency=1000, duty_cycle=0)

# vcgencmd get_rsts, 1000 = power on, 1020 = reset button, 20 = sudo reboot
# vcgencmd get_throttled to log undervoltage, overtemp etc



try:
    haptic = adafruit_drv2605.DRV2605(i2c_sys) # 0x5A
    haptic.use_LRM()
    haptic.sequence[0] = adafruit_drv2605.Effect(5) # effect 1: strong click, 4: sharp click 100%, 5: sharp click 60%,  24: sharp tick,  27: short double click strong, 16: 1000 ms alert, 21: medium click, 
except Exception as e:
    haptic = None
    #TODO: logger.error(f"Error setting up haptic engine: {e}")
    
# autocal results with DRIVE_TIME / 0x1B[4:0] = 25, RATED_VOLTAGE / reg 0x16 = 104, OD_CLAMP / 0x17 = 150
# >>> haptic._read_u8(0x18)
# 12
# >>> haptic._read_u8(0x19)
# 209
# >>> haptic._read_u8(0x1A)
# 182

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
for addr in range(0x20, 0x28):
    try:
        port_expanders.append(MCP23017(i2c_ext1, address=addr))
    except: # ValueError if device does not exist, ignore
        pass
# second bus/connector      
#for addr in range(0x20, 0x28):
#    try:
#        port_expanders.append(MCP23017(i2c_ext2, address=addr))
#    except: # ValueError if device does not exist, ignore
#        pass

compartments = {}
        
# initializes the port expanders and compartmnts
# input: the number of desired large compartments
# returns: the list of accessible/present compartments
def init_port_expanders(large_compartments):
    # for V2, large compartments can be on connector 6 of each PCB
    # starting with PCB 1, going to 2 and 3 if 3 compartments are present
    # create compartment objects with IO ports, and a dict for all of them
    # first numerical for small comps and then alphabetical for large comps
    
    compartments_per_row = 5
    global port_expanders, compartments

    counter = 1
    # normal compartments
    for index, expander in enumerate(port_expanders):
        # enable PCB activity LED
        LED_pin = expander.get_pin(15)
        LED_pin.direction = digitalio.Direction.OUTPUT
        LED_pin.value = True
        for compartment_per_expander in range(compartments_per_row):
            space = index * compartments_per_row + compartment_per_expander + 1
            
            input_pin = expander.get_pin(compartment_per_expander * 2)
            output_pin = expander.get_pin(compartment_per_expander * 2 + 1)
            new_compartment = compartment.compartment(input_pin, output_pin)
            new_compartment.LEDs = [space - 1]
            new_compartment.LED_connector = LED_connector_1
            compartments[f"{counter}"] = new_compartment
            counter += 1
            
    # large compartments
    counter = 0
    for index, large_compartment in enumerate(large_compartments):
        if len(port_expanders) > index:
            expander = port_expanders[index]
            input_pin = expander.get_pin(compartments_per_row * 2)
            output_pin = expander.get_pin(compartments_per_row * 2 + 1)
            new_compartment = compartment.compartment(input_pin, output_pin)
            new_compartment.LEDs = [counter]
            new_compartment.LED_connector = LED_connector_3
            compartments[large_compartment] = new_compartment
            counter += 1
