#
# Schlüsselkasten V2 Hardware SETUP
#

import board
import digitalio
from adafruit_extended_bus import ExtendedI2C as I2C

from adafruit_mcp230xx.mcp23017 import MCP23017 # port expander
import adafruit_lis3dh # accelerometer
import adafruit_veml7700 # light sensor
import adafruit_drv2605 # haptic driver

import subprocess  # For executing a shell command
import logging
import time

import compartment

from pi5neo import Pi5Neo as SPIneo

from rpi_hardware_pwm import HardwarePWM

from math import floor

logger = logging.getLogger(__name__)

# infos
__version__ = "2.0.0-beta1"

nfc_serial = "/dev/ttyAMA3"

    
# 4 separate buses on V2
i2c_sys = I2C(4)  # Device is /dev/i2c-4
i2c_ext1 = I2C(1)  # Device is /dev/i2c-1
i2c_ext2 = I2C(5)  # Device is /dev/i2c-5
i2c_ee = I2C(0)  # Device is /dev/i2c-0

# PWM
# display backlight
backlight = HardwarePWM(pwm_channel=1, hz=10000, chip=0)
backlight.start(50) 

# piezo buzzer
piezo = HardwarePWM(pwm_channel=0, hz=1000, chip=0)

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
LED_connector_1 = SPIneo('/dev/spidev1.0', 40, 1200)
#LED_connector_2 = SPIneo('/dev/spidev4.0', 40, 1000)
LED_connector_3 = SPIneo('/dev/spidev0.0', 3, 1000, "RGBW")

LED_connector_1.clear_strip()
LED_connector_1.update_strip(sleep_duration=0.001)
#LED_connector_2.clear_strip()
#LED_connector_2.update_strip(sleep_duration=0.001)
LED_connector_3.clear_strip()
LED_connector_3.update_strip(sleep_duration=0.001)


try:
    haptic = adafruit_drv2605.DRV2605(i2c_sys) # 0x5A
    haptic.use_LRM()
    haptic.sequence[0] = adafruit_drv2605.Effect(26) # effect 1: strong click, 4: sharp click 100%, 5: sharp click 60%,  24: sharp tick, 25-26 weaker ticks,  27: short double click strong, 16: 1000 ms alert, 21: medium click, 
except Exception as e:
    haptic = None
    logger.error(f"Error setting up haptic engine: {e}")
    
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
    logger.error(f"Error setting up accelerometer: {e}")

try:
    light_sensor = adafruit_veml7700.VEML7700(i2c_sys) # 0x10 read: light_sensor.lux
except Exception as e:
    light_sensor = None
    logger.error(f"Error setting up brightness sensor: {e}")

try: 
    # TODO: add support for the BQ34210
    battery_monitor = None
except Exception as e:
    battery_monitor = None
    logger.error(f"Error setting up battery monitor: {e}")

# get connected port expanders on two buses (adresses from 0x20 to 0x27, prototype PCBs: 0x24 to 0x27)
# first bus/connector        
port_expanders = []
for addr in range(0x20, 0x28):
    try:
        port_expanders.append(MCP23017(i2c_ext1, address=addr))
    except ValueError: # ValueError if device does not exist, ignore
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
    
    compartments_per_row = 5
    global port_expanders, compartments

    counter = 1
    # normal compartments, 1 to n*5 (n = number of port expanders)
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
            
    # large compartments, n*5 + 1 to n*5 + n (e.g. 21 to 24 for n = 4)
    for index in range(large_compartments):
        if len(port_expanders) > index:
            expander = port_expanders[index]
            input_pin = expander.get_pin(compartments_per_row * 2)
            output_pin = expander.get_pin(compartments_per_row * 2 + 1)
            new_compartment = compartment.compartment(input_pin, output_pin)
            new_compartment.LEDs = [index]
            new_compartment.LED_connector = LED_connector_3
            compartments[f"{counter}"] = new_compartment
            counter += 1
            
# check door of all compartments
def check_all():
    open_comps = []
    for index in range(len(compartments)):
        if compartments[str(index + 1)].is_open():
            open_comps.append(str(index + 1))
    return open_comps
    
# open all compartments
def open_all():
    for index in range(len(compartments)):
        compartments[str(index + 1)].open()
        
# open compartments for mounting (block corners)
def open_mounting():
    for block in range(floor(len(compartments) / 20)):
        compartments[f"{1+20*block}"].open()
        compartments[f"{5+20*block}"].open()
        compartments[f"{16+20*block}"].open()
        compartments[f"{20+20*block}"].open()
        
def get_cpu_serial():
    try:
        with open("/sys/firmware/devicetree/base/serial-number") as f:
            return(f.read().strip('\x00'))
    except Exception as e:
        logger.warning(f"Error reading RPi serial: {e}")
        return "None"

def get_cpu_model():
    try:
        with open("/sys/firmware/devicetree/base/model") as f:
            return(f.read().strip('\x00'))
    except Exception as e:
        logger.warning(f"Error reading cpu model: {e}")
        return "None"
        
def get_ESSID():
    try:
        result = subprocess.run("iw dev wlan0 link | grep SSID", capture_output=True, text=True, shell=True)
        return result.stdout.strip()[6:]
    except Exception:
        return None
    
def get_RSSI():
    try:
        result = subprocess.run("iw dev wlan0 link | grep signal", capture_output=True, text=True, shell=True)
        return result.stdout.strip()[8:]
    except Exception:
        return None
    
def get_sys_messages():
    try:
        result = subprocess.run("vcgencmd get_throttled", capture_output=True, text=True, shell=True)
        
        hex_value = result.stdout.strip().split("=")[1]
        throttled = int(hex_value, 16)
        # Bit definitions
        status_bits = {
            0: "Under-voltage detected",
            1: "Arm frequency capped",
            2: "Currently throttled",
            3: "Soft temperature limit active",
            16: "Under-voltage occurred since last reboot",
            17: "Arm frequency capped since last reboot",
            18: "Throttling occurred since last reboot",
            19: "Soft temperature limit occurred"
        }
        messages = {}
        # Check each bit and print the status
        for bit, message in status_bits.items():
            if throttled & (1 << bit):
                messages[bit] = message
        
        return messages
    except Exception:
        return None

def get_temp():
    try:
        result = subprocess.run("vcgencmd measure_temp", capture_output=True, text=True, shell=True)
        return result.stdout.strip().split("=")[1][:-2]
    except Exception:
        return None
        
def uptime():
    try:
        result = subprocess.run("uptime", capture_output=True, text=True, shell=True)
        return result.stdout.strip()
    except Exception:
        return None

def beep(duration=0.1, frequency=1000):
    piezo.change_frequency(frequency)
    piezo.start(50)
    time.sleep(duration)
    piezo.stop()

