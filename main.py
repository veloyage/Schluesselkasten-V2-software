import flet as ft
import time
import platform

from tomlkit.toml_file import TOMLFile

import logging

#import compartment
import ui
import hardware_V2 as hardware
#import hardware_mock as hardware
import flink
import helpers
import networking
from nfc import NFC

import subprocess

# TODO: GUi watchdog: if no interaction for time x, go back to welcome page

# version string
__version__ = "2.0.0-alpha3"

#
# functions
#


# background tasks function
def background_tasks(ui):
    counter = 0      
    while True:
        # check connectivity and update icon, reconnect handled at system level
        
        #ui.no_wifi_grid.hidden = networking.ping()

        # check grid power connection
        #ui.no_power_grid.hidden = True # disabled, unreliable # hardware.supply_present.value
        

        if hardware.light_sensor is not None:
            try:
                ambient_brightness = hardware.light_sensor.lux  # check brightness
                display_brightness = settings["min_backlight"] + (100 - settings["min_backlight"]) * ambient_brightness/settings["max_brightness"]
                if display_brightness > 100:
                    display_brightness = 100
                hardware.backlight.change_duty_cycle(display_brightness)
                #hardware.LED_internal.brightness = 0.1 + 0.9 * light / 100
                #hardware.LED_connector_1.brightness = 0.1 + 0.9 * light / 100
                #hardware.LED_connector_2.brightness = 0.1 + 0.9 * light / 100
            except Exception as e:
                logger.error(f"Error getting ambient brightness: {e}")


        if counter == 300:  # runs roughly every 5 minutes
            counter = 0
            # send status as keepalive
            status_code = flink.put_status(time.monotonic(), SN, __version__, small_compartments, large_compartments)
            if status_code != 200:
                logger.warning(f"Response from Flink: {status_code}.")
                #ui.no_flink_grid.hidden = False
            else:
                #ui.no_flink_grid.hidden = True
                pass

            # check battery status
            if hardware.battery_monitor is not None:
                if hardware.battery_monitor.cell_voltage < 3.5:  # log if low battery
                    logger.warning(f"Battery low: {battery_monitor.cell_voltage:.2f}V, {battery_monitor.cell_percent:.1f} %")
                    #ui.low_battery_grid.hidden = False
                else:
                    #ui.low_battery_grid.hidden = True
                    pass
                    
        # check if NFC tag is present, timeout=1s                       
        if (ui.returning in ui.page or ui.welcome in ui.page) and nfc is not None:
            uid = nfc.check()               
            if uid is not None:
                logging.info(f"NFC tag with UID {uid} was scanned.")                
                for comp, comp_tags in settings["NFC-tags"].items():
                    if uid in comp_tags:
                        if comp == "service":
                            ui.page_reconfigure(ui.service)
                        else:
                            ui.open_compartment(comp, "return")
        else:
            time.sleep(1)
        counter += 1

#
# LOAD SETTINGS
#

toml = TOMLFile("settings.toml")
settings = toml.read()
ID = settings["ID"]
SN = settings["SN"]
HW_revision = settings["HW_revision"]

small_compartments = settings["SMALL_COMPARTMENTS"]
large_compartments = settings["LARGE_COMPARTMENTS"]

aio_username = settings["ADAFRUIT_IO_USERNAME"]
aio_key = settings["ADAFRUIT_IO_KEY"]
aio_feed_name = settings["ADAFRUIT_IO_FEED"]

   
#
# LOGGING SETUP
#
  
# open local logfile
logger = logging.getLogger(__name__)

logging.basicConfig(filename='schlüsselkasten.log',
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

logger.info("-------------")
logger.info("Logging to disk started.")

logger.addHandler(flink.FlinkLogHandler(logging.ERROR, ID, settings["FLINK_URL"], settings["FLINK_API_KEY"]))
logger.info("Logging to Flink started.")

mqtt = networking.init_mqtt(settings["ADAFRUIT_IO_USERNAME"], settings["ADAFRUIT_IO_KEY"], settings["ADAFRUIT_IO_FEED"])
if mqtt is not None:
    logger.addHandler(networking.AIOLogHandler(logging.INFO, mqtt))
    logger.info("Logging to MQTT broker started.")


#
# INFO MESSAGES
#
logger.info(f"Ziemann Engineering Schlüsselkasten {ID}")
logger.info(f"Serial number {SN}, standard compartments: {small_compartments}, large compartments: {large_compartments}")
logger.info(f"Software: {__version__}, Python: {platform.python_version()}, OS: {platform.platform()}")
logger.info(f"Hardware revision: {HW_revision}, Platform: {hardware.platform}")
#logger.info(f"CPU ID: {hex_format(microcontroller.cpu.uid)}, temperature: {microcontroller.cpu.temperature:.2}°C")
#logger.info(f"Reset reason: {str(microcontroller.cpu.reset_reason).split('.')[2]}, run reason: {str(supervisor.runtime.run_reason).split('.')[2]}")

if networking.ping() is True:
    logger.info(f"Ping to google successful.")
else:
    logger.warning("Ping to google failed.")

flink = flink.Flink(ID, settings["FLINK_URL"], settings["FLINK_API_KEY"])
status_code = flink.put_status(time.monotonic(), SN, __version__, small_compartments, large_compartments)
if status_code == 200:
    logger.info(f"Response from Flink: {status_code}.")
else:
    logger.warning(f"Response from Flink: {status_code}.")
    #ui.no_flink_grid.hidden = False

#
# HARDWARE SETUP
#

if hardware.battery_monitor is not None:
    logger.info(f"Battery status: {hardware.battery_monitor.cell_voltage:.2f}V, {hardware.battery_monitor.cell_percent:.1f} %")

logger.info(f"{len(hardware.port_expanders)} compartment PCBs / rows detected.")
if len(hardware.port_expanders)*8 < small_compartments:
    logger.error("Insufficient compartment PCBs detected.")
    #ui.maintainance_grid.hidden = False

# initialize the compartment PCBs / port expanders
hardware.init_port_expanders(large_compartments)

try: 
    nfc = NFC(settings["NFC"], hardware.nfc_serial)
except Exception as e:
    nfc = None
    logger.error(f"Error setting up NFC: {e}")
    

open_comps = helpers.check_all(hardware.compartments)
if len(open_comps) != 0:
    logger.warning(f"Open compartments: {open_comps}")

#
# Start GUI
#

ft.app(target=ui.UI(settings, toml, flink, nfc, background_tasks))