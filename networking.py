from Adafruit_IO import MQTTClient
import logging

import platform    # For getting the operating system name
import subprocess  # For executing a shell command

import ping3

from hardware_V2 import compartments

import helpers

logger = logging.getLogger(__name__)


def ping():
    return ping3.ping("google.com", unit='ms')

#
# MQTT
#

# Callback function which will be called when a connection is established
def connected(mqtt):
    mqtt.subscribe(mqtt.feed_name + "-command")

# Callback function which will be called when a message comes from a subscribed feed
def message(mqtt, feed_id, payload):
    if feed_id == (mqtt.feed_name + "-command"):
        process_mqtt_command(payload)
        
def disconnected(mqtt):
    # Disconnected function will be called when the mqtt disconnects.
    sys.exit(1)

def init_mqtt(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY, aio_feed_name):
    # try to connect to MQTT broker and use it for logging
    
    # Create an MQTT instance.
    mqtt = MQTTClient(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)
    
    # Setup the callback functions defined above.
    mqtt.on_connect    = connected
    mqtt.on_disconnect = disconnected
    mqtt.on_message    = message
    mqtt.feed_name = aio_feed_name
    
    try:
        # Connect to the Adafruit IO server.
        mqtt.connect()

        # Runs a thread in the background 
        mqtt.loop_background()
        return mqtt
    except Exception as e:
        logger.error(f"Error connecting to MQTT broker: {e}")
        return None
          

# process received command
def process_mqtt_command(payload):
    payload = payload.split(" ")
    command = payload[0]
    if command == "status" and len(payload) == 2:
        comp = payload[1]
        if comp == "all":
            logger.info(f"Open compartments: {helpers.check_all(compartments)}")
        elif int(comp) > 0 and int(comp) <= len(compartments):
            logger.info(f"Compartment {comp} status: door open: {compartments[comp].get_inputs()}, door status saved: {compartments[comp].door_status}, content status: {compartments[comp].content_status}.")
    elif command == "open" and len(payload) == 2:
        comp = payload[1]
        if comp == "all":
            helpers.open_all(compartments)
        elif int(comp) > 0 and int(comp) <= len(compartments):
            compartments[comp].open()
        logger.info(f"Compartment open sent from MQTT broker: {comp}")
    elif command == "reset" and len(payload) == 1:
       subprocess.call("./start.sh")
    #elif command == "service" and len(payload) == 1:    
       #UI.page_reconfigure(UI.service)
    #elif command == "tamper_alarm" and len(payload) == 2:
        # global tamper_alarm
        # if payload[1] == "off":
            # tamper_alarm = "off"
        # elif payload[1] == "on":
            # tamper_alarm = "on"

class AIOLogHandler(logging.Handler):
    def __init__(self, level, mqtt):
        super().__init__(level)
        self.mqtt = mqtt
    def emit(self, record):
        try:
            self.mqtt.publish(self.mqtt.feed_name + "-status", self.format(record))
        except Exception as e:  # logging would trigger further exceptions
            print(f"Error when logging to MQTT broker: {e}")