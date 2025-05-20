import logging
import flink
import subprocess

logger = logging.getLogger(__name__)

# check door of all compartments
def check_all(compartments):
    open_comps = []
    for index in range(len(compartments)):
        if compartments[str(index + 1)].get_inputs():
            open_comps.append(str(index + 1))
    return open_comps
    
# open all compartments
def open_all(compartments):
    for index in range(len(compartments)):
        compartments[str(index + 1)].open()
        
# open compartments for mounting (bottom left and right)
def open_mounting(compartments):
    if len(compartments) >= 20:
        compartments["16"].open()
        compartments["20"].open()
    if len(compartments) >= 40:
        compartments["36"].open()
        compartments["40"].open()
    if len(compartments) >= 60:
        compartments["56"].open()
        compartments["60"].open()
        
def get_rpi_serial():
    try:
        with open("/sys/firmware/devicetree/base/serial-number") as f:
            return(f.read())
    except Exception as e:
        logger.warning(f"Error reading RPi serial: {e}")
        return "None"

def get_rpi_model():
    try:
        with open("/sys/firmware/devicetree/base/model") as f:
            return(f.read())
    except Exception as e:
        logger.warning(f"Error reading RPi model: {e}")
        return "None"
        
def get_ESSID():
    try:
        result = subprocess.run("iw dev wlan0 link | grep SSID", capture_output=True, text=True, shell=True)
        return result.stdout.strip()[6:]
    except:
        return None
    
def get_RSSI():
    try:
        result = subprocess.run("iw dev wlan0 link | grep signal", capture_output=True, text=True, shell=True)
        return result.stdout.strip()[8:]
    except:
        return None
    
def get_throttled():
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
    except:
        return None

def get_temp():
    try:
        result = subprocess.run("vcgencmd measure_temp", capture_output=True, text=True, shell=True)
        return result.stdout.strip().split("=")[1][:-2]
    except:
        return None
        
def uptime():
    try:
        result = subprocess.run("uptime", capture_output=True, text=True, shell=True)
        return result.stdout.strip()
    except:
        return None