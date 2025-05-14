import flet as ft
import time
import platform

from tomlkit.toml_file import TOMLFile

import logging

#import compartment
#import ui
import hardware_V2 as hardware
#import hardware_mock as hardware
import flink
import helpers
import networking
from nfc import NFC

import subprocess

# ZE colors: "#006688" and "#8ff040"
# TODO: GUi watchdog: if no interaction for time x, go back to welcome page

# version string
__version__ = "2.0.0-alpha1"

class DigitButton(ft.ElevatedButton):
    def __init__(self, button_clicked, text = None):
        super().__init__()
        self.text = text
        self.on_click = button_clicked
        self.data = text
        self.expand = 1
        self.padding = 0
        self.style=ft.ButtonStyle(text_style=ft.TextStyle(size=60, weight=ft.FontWeight.BOLD), shape=ft.RoundedRectangleBorder(radius=30))#, weight=ft.FontWeight.BOLD))
        self.bgcolor = ft.Colors.WHITE
        self.color = "#006688"


class NumberPad(ft.Container):
    def __init__(self, callback):
        super().__init__()
        self.number = ""
        self.callback = callback
        self.content = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        DigitButton(text="1", button_clicked=self.button_clicked),
                        DigitButton(text="2", button_clicked=self.button_clicked),
                        DigitButton(text="3", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="4", button_clicked=self.button_clicked),
                        DigitButton(text="5", button_clicked=self.button_clicked),
                        DigitButton(text="6", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="7", button_clicked=self.button_clicked),
                        DigitButton(text="8", button_clicked=self.button_clicked),
                        DigitButton(text="9", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        ft.ElevatedButton(content=ft.Icon(name=ft.Icons.CLOSE, color=ft.Colors.RED, size=78),
                            bgcolor = ft.Colors.WHITE, 
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=30)), 
                            on_click=self.button_clicked, 
                            data="x",
                            expand=1),
                        DigitButton(text="0", button_clicked=self.button_clicked),
                        ft.ElevatedButton(content=ft.Icon(name=ft.Icons.CHECK, color=ft.Colors.GREEN, size=78),
                            bgcolor = ft.Colors.WHITE, 
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=30)), 
                            on_click=self.button_clicked, 
                            data="ok",
                            expand=1),
                    ]
                ),
            ]
        )

    def button_clicked(self, e):
        data = e.control.data
        self.callback(data)

    

class UI():
    def __init__(self):
        self.__page = None
        
    def __call__(self, flet_page: ft.Page):
        self.page = flet_page
        self.page.title = "Schlüsselkasten V2"
        self.page.window.height = 800
        self.page.window.width = 480
        self.page.window.frameless = True
        self.page.window.full_screen = True
        self.page.bgcolor = ft.Colors.GREY_200
        self.page.theme = ft.Theme(color_scheme_seed="#006688")
         
        # all the different page setups
        
        self.welcome = ft.Column(
                        controls=[
                            ft.Card(ft.Container(ft.Image(src=f"logo.png", width=800, height=100, fit=ft.ImageFit.CONTAIN,), padding=10), color=ft.Colors.WHITE, margin=0),
                            ft.Card(content=ft.Container(content=ft.Text(value="Willkommen beim Schlüsselkasten von Ziemann Engineering. \nWas möchtest du tun?", color="#006688", text_align=ft.TextAlign.LEFT, size=35, style=ft.TextStyle(weight=ft.FontWeight.BOLD)), padding=15),color=ft.Colors.WHITE, margin=0),
                            ft.ElevatedButton(on_click=lambda _: self.page_reconfigure(self.booking), icon=ft.Icons.EVENT, icon_color=ft.Colors.WHITE, text=" Buchen", color = ft.Colors.WHITE, bgcolor = "#006688", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=30), padding=20, icon_size=45, text_style=ft.TextStyle(size=35))),
                            ft.ElevatedButton(on_click=lambda _: self.page_reconfigure(self.borrowing), icon=ft.Icons.OUTPUT,icon_color=ft.Colors.WHITE, text=" Ausleihen", color = ft.Colors.WHITE, bgcolor = "#006688", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=30), padding=20, icon_size=45, text_style=ft.TextStyle(size=35))),
                            ft.ElevatedButton(on_click=lambda _: self.page_reconfigure(self.returning), icon=ft.Icons.EXIT_TO_APP,icon_color=ft.Colors.WHITE, text=" Zurückgeben", color = ft.Colors.WHITE, bgcolor = "#006688", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=30), padding=20, icon_size=45, text_style=ft.TextStyle(size=35))),
                        ],
                        spacing=30
                    )
                    
        self.help = ft.Column(
                        controls=[
                            ft.Card(content=ft.Container(content=ft.Text(value="Kurzanleitung", color="#006688", text_align=ft.TextAlign.LEFT, size=35, style=ft.TextStyle(weight=ft.FontWeight.BOLD)), padding=10),color=ft.Colors.WHITE, margin=0),
                            ft.Card(content=ft.Container(content=ft.Text(value="An diesem Schlüsselkasten kannst du Schlüssel und andere Gegenstände ausleihen. So gehts:", color="#006688", text_align=ft.TextAlign.LEFT, size=19, style=ft.TextStyle(weight=ft.FontWeight.BOLD)), padding=10, margin=0, expand=True),color=ft.Colors.WHITE, margin=0),
                            ft.Card(content=ft.Row([
                                ft.Container(ft.Icon(name=ft.Icons.EVENT, color="#006688", size=45), padding=10),
                                ft.Container(content=ft.Text(value="Zuerst musst du über Flink buchen. Wenn du noch keinen Zugang zu Flink hast, wende dich bitte zu den Öffnungszeiten an die Rezeption.", color="#006688", text_align=ft.TextAlign.LEFT, size=19, style=ft.TextStyle(weight=ft.FontWeight.BOLD)), padding=10, margin=0, expand=True)
                                ], spacing=0),
                                color=ft.Colors.WHITE, margin=0),
                            ft.Card(content=ft.Row([
                                ft.Container(ft.Icon(name=ft.Icons.OUTPUT, color="#006688", size=45), padding=10),
                                ft.Container(content=ft.Text(value="Nach Beginn des gebuchten Zeitraums kannst du den erhaltenen Code hier eingeben. Das entsprechende Fach öffnet sich und du kannst den Inhalt entnehmen.", color="#006688", text_align=ft.TextAlign.LEFT, size=19, style=ft.TextStyle(weight=ft.FontWeight.BOLD)), padding=10, margin=0, expand=True)
                                ], spacing=0),
                                color=ft.Colors.WHITE, margin=0),
                            ft.Card(content=ft.Row([
                                ft.Container(ft.Icon(name=ft.Icons.EXIT_TO_APP, color="#006688", size=45), padding=10),
                                ft.Container(content=ft.Text(value="Bitte komme vor Ende deiner Buchung zurück und halte den Schlüsselanhänger rechts an das Lesegerät. Das Fach öffnet sich dann für die Rückgabe.", color="#006688", text_align=ft.TextAlign.LEFT, size=19, style=ft.TextStyle(weight=ft.FontWeight.BOLD)), padding=10, margin=0, expand=True)
                                ], spacing=0),
                                color=ft.Colors.WHITE, margin=0),
                            ft.Card(content=ft.Row([
                                ft.Container(ft.Icon(name=ft.Icons.WARNING, color="#006688", size=45), padding=10),
                                ft.Container(content=ft.Text(value="Wenn du ein Problem hast, wende dich bitte zu den Öffnungszeiten an die Rezeption.", color="#006688", text_align=ft.TextAlign.LEFT, size=19, style=ft.TextStyle(weight=ft.FontWeight.BOLD)), padding=10, margin=0, expand=True)
                                ], spacing=0),
                                color=ft.Colors.WHITE, margin=0),
                        ],
                        spacing=10
                    )
        
        self.compartment  = ""  
        self.service_mode = ft.RadioGroup(content=ft.Column([
                                ft.Radio(value="open", label="Einzelnes Fach öffnen", label_style=ft.TextStyle(color="#006688", weight=ft.FontWeight.BOLD, size=20), active_color="#006688"),
                                ft.Radio(value="program", label="NFC-Tag einem Fach zuweisen", label_style=ft.TextStyle(color="#006688", weight=ft.FontWeight.BOLD, size=20), active_color="#006688"),
                                ft.Radio(value="reset", label="Fach-Tag-Zuweisung zurücksetzen", label_style=ft.TextStyle(color="#006688", weight=ft.FontWeight.BOLD, size=20), active_color="#006688")]))
        self.service_mode.value = "open"                        
        self.service = ft.Column(
                        controls=[
                            ft.Card(content=ft.Container(content=ft.Text(value="Service-Menü", color="#006688", text_align=ft.TextAlign.LEFT, size=35, style=ft.TextStyle(weight=ft.FontWeight.BOLD)), padding=15),color=ft.Colors.WHITE, margin=0),
                            ft.Row([
                                ft.ElevatedButton(text="App schliessen",on_click=lambda _: self.page.window.close(), color = ft.Colors.WHITE, bgcolor = "#006688", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=30), padding=20, text_style=ft.TextStyle(size=20, weight=ft.FontWeight.BOLD)), expand=True),
                                ft.ElevatedButton(text="App neustarten", on_click=lambda _: subprocess.call("./start.sh"), color = ft.Colors.WHITE, bgcolor = "#006688", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=30), padding=20, text_style=ft.TextStyle(size=20, weight=ft.FontWeight.BOLD)), expand=True),
                                ]),
                            ft.Row([
                                ft.ElevatedButton(text="Alle Fächer öffnen",on_click=self.open_all_clicked, color = ft.Colors.WHITE, bgcolor = "#006688", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=30), padding=20, text_style=ft.TextStyle(size=20, weight=ft.FontWeight.BOLD)), expand=True),
                                ft.ElevatedButton(text="Montage-Modus", on_click=self.mounting_clicked, color = ft.Colors.WHITE, bgcolor = "#006688", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=30), padding=20, text_style=ft.TextStyle(size=20, weight=ft.FontWeight.BOLD)), expand=True),
                                ]),
                            ft.Card(ft.Container(self.service_mode, padding = 10), color=ft.Colors.WHITE, margin=0),
                            NumberPad(self.service_callback)
                        ],
                        spacing=20
                    )
        
        self.booking = ft.Column(
                        controls=[
                            ft.Card(content=ft.Container(content=ft.Text(value="Buchung", color="#006688", text_align=ft.TextAlign.LEFT, size=35, style=ft.TextStyle(weight=ft.FontWeight.BOLD)), padding=15),color=ft.Colors.WHITE, margin=0),
                            ft.Card(content=ft.Container(content=ft.Text(value="Buchen kannst du via Flink (App oder Webseite). Hier ist ein Link als QR-Code:", color="#006688", text_align=ft.TextAlign.LEFT, size=20, style=ft.TextStyle(weight=ft.FontWeight.BOLD)), padding=15, margin=0, expand=True),color=ft.Colors.WHITE, margin=0),
                            ft.Card(ft.Container(ft.Image(src=f"qrcode.png", width=450, height=480, fit=ft.ImageFit.CONTAIN,), padding=15), color=ft.Colors.WHITE, margin=0),
                        ],
                        spacing=20
                    )
        
        self.code  = ""  
        self.code_display = ft.Text(value=self.code, size=180, color="#006688", width = 460, max_lines=1, style=ft.TextStyle(height=0.9))
        self.borrowing = ft.Column(
                        controls=[
                        ft.Card(content=ft.Container(content=ft.Text(value="Ausleihe", color="#006688", text_align=ft.TextAlign.LEFT, size=35, style=ft.TextStyle(weight=ft.FontWeight.BOLD)), padding=15),color=ft.Colors.WHITE, margin=0),
                        ft.Card(ft.Container(ft.Text(value="Bitte gib deinen vierstelligen Code ein.", size=20, color="#006688", style=ft.TextStyle(weight=ft.FontWeight.BOLD)), padding=10), color=ft.Colors.WHITE),
                        ft.Card(ft.Container(self.code_display, padding=10), color=ft.Colors.WHITE), 
                        NumberPad(self.borrowing_callback)
                        ],
                        #spacing=20
                    )
        
        self.returning = ft.Column(
                        controls=[
                            ft.Card(content=ft.Container(content=ft.Text(value="Rückgabe", color="#006688", text_align=ft.TextAlign.LEFT, size=35, style=ft.TextStyle(weight=ft.FontWeight.BOLD)), padding=15),color=ft.Colors.WHITE, margin=0),
                            ft.Card(content=ft.Row([
                                ft.Container(content=ft.Text(value="Bitte halte den Schlüsselanhänger an das Lesegerät auf der rechten Seite des Kastens.", color="#006688", text_align=ft.TextAlign.LEFT, size=20, style=ft.TextStyle(weight=ft.FontWeight.BOLD)), padding=10, margin=10, expand=True), 
                                ft.Icon(name=ft.Icons.ARROW_FORWARD, color="#006688", size=100)]),
                            color=ft.Colors.WHITE, margin=0),
                            ft.Card(ft.Container(ft.Image(src=f"nfc2.png", width=430, height=390, fit=ft.ImageFit.CONTAIN,), padding=15), color=ft.Colors.WHITE, margin=0),
                        ],
                        spacing=20
                    )
        
      
        self.info_bar = ft.Container(
                content=ft.Row([
                ft.Text(value="Status:", color=ft.Colors.WHITE, size=20),
                ft.Icon(name=ft.Icons.CLOUD_OFF, color=ft.Colors.WHITE),
                ft.Icon(name=ft.Icons.WIFI_OFF, color=ft.Colors.WHITE),
                #ft.Icon(name=ft.Icons.POWER_OFF, color=ft.Colors.WHITE),
                #ft.Icon(name=ft.Icons.BATTERY_0_BAR, color=ft.Colors.WHITE),
                #ft.Icon(name=ft.Icons.ENGINEERING, color=ft.Colors.WHITE)
            ],
            alignment=ft.MainAxisAlignment.CENTER))
        
        self.page.appbar = ft.AppBar(
            leading_width=48,
            leading=ft.IconButton(on_click=lambda _: self.page_reconfigure(self.welcome), icon=ft.Icons.ARROW_BACK,icon_color=ft.Colors.WHITE, icon_size=30, padding=ft.padding.all(12)),
            title=ft.Text("Ziemann Engineering Schlüsselkasten", size=20, color=ft.Colors.WHITE),
            #title=info_bar,
            center_title=True,
            actions=[ft.IconButton(on_click=lambda _: self.page_reconfigure(self.help), icon=ft.Icons.HELP_OUTLINE,icon_color=ft.Colors.WHITE, icon_size=30, padding=ft.padding.all(12))],
            bgcolor="#006688",   
        )       
        
        self.page.add(self.welcome)        
        self.page.update()
        
        #
        ### Do background tasks
        #
        counter = 0
        min_backlight = 3 # minimum screen brightness in %
        max_brightness = 50 # screen is at maximum brightness at this lux level
       
        while True:
            # check connectivity and update icon, reconnect handled at system level
            
            #ui.no_wifi_grid.hidden = networking.ping()

            # check grid power connection
            #ui.no_power_grid.hidden = True # disabled, unreliable # hardware.supply_present.value
            

            if hardware.light_sensor is not None:
                try:
                    ambient_brightness = hardware.light_sensor.lux  # check brightness
                    display_brightness = min_backlight + (100 - min_backlight) * ambient_brightness/max_brightness
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
            if (self.returning in self.page or self.welcome in self.page) and nfc is not None:
                uid = nfc.check()               
                if uid is not None:
                    logging.info(f"NFC tag with UID {uid} was scanned.")                
                    for comp, comp_tags in settings["NFC-tags"].items():
                        if uid in comp_tags:
                            if comp == "service":
                                self.page_reconfigure(self.service)
                            else:
                                self.open_compartment(comp, "return")
            else:
                time.sleep(1)
            counter += 1
        
    # switch between welcome (initial), booking, borrowing, returning and service pages
    def page_reconfigure(self, destination):
        if len(self.page.controls) > 0:
           self.page.remove_at(0)
        self.page.add(destination)
        self.page.update()
        
    def borrowing_callback(self, data):
        if data == "x":
            self.code = ""
        elif data == "ok":
            comp, status = check_code(self.code)
            if status == "valid":
                self.open_compartment(comp, "borrow")
                logger.info(f"Code '{self.code}' was entered, valid for compartment {comp}, content status: {hardware.compartments[comp].content_status}, door status: {hardware.compartments[comp].door_status}.")
            else:
                if status=="invalid":
                    title = "Code ungültig"
                    announcement = "Dieser Code ist aktuell nicht gültig. Bitte prüfe deine Buchung."
                else:
                    title = "Fehler"
                    announcement = "Beim Prüfen des Codes ist ein Fehler aufgetreten. Bitte versuche es später nochmals."
                dlg = ft.AlertDialog(
                    modal=False,
                    title=ft.Text(title),
                    content=ft.Text(announcement, style=ft.TextStyle(size=20)),
                    on_dismiss=None,
                    #barrier_color="#66660000"
                    )
                self.page.open(dlg)
                time.sleep(5)
                self.page.close(dlg)
                logger.info(f"Code '{self.code}' was entered, but the code check returned: {status}.")
            self.code = ""
        else:
            self.code = self.code + data

        self.code_display.value = self.code
        self.page.update()
        
    def service_callback(self, data):
        if data == "x":
            self.compartment = ""
        elif data == "ok":
            if self.service_mode.value == "open":
                success = self.open_compartment(self.compartment, "service")
                if success:
                    logger.info(f"Compartment {self.compartment} was opened from service mode, content status: {hardware.compartments[self.compartment].content_status}, door status: {hardware.compartments[self.compartment].door_status}.")
            elif self.service_mode.value == "program":
                # nfc_personalize, write dict, save to toml
                dlg_modal = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("NFC-Tag programmieren"),
                    content=ft.Text(f"Bitte den NFC-Tag für Fach {self.compartment} rechts an den Leser halten, bis der Vorgang abgeschlossen ist.", style=ft.TextStyle(size=20)),
                    actions=[ft.TextButton("Abbrechen", on_click=lambda e: self.page.close(dlg_modal), style=ft.ButtonStyle(text_style=ft.TextStyle(size=20, weight=ft.FontWeight.BOLD)))],
                    on_dismiss=None)
                self.page.open(dlg_modal)
                if nfc is not None:
                    uid = nfc.personalize()
                self.page.close(dlg_modal)
                if uid is not None:
                    settings["NFC-tags"][self.compartment].append(uid)
                    logger.info(f"NFC tag with UID {uid} assigned to compartment {self.compartment}.")
                    toml.write(settings)
                else:
                    logger.warning(f"Tag assignment failed, no NFC tag found.")
            elif self.service_mode.value == "reset":
                # write dict, save to toml
                dlg_modal = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Fach zurückgesetzt"),
                    content=ft.Text(f"Die gespeicherten NFC-Tags für Fach {self.compartment} wurden gelöscht.", style=ft.TextStyle(size=20)),
                    on_dismiss=None)
                self.page.open(dlg_modal)
                settings["NFC-tags"][self.compartment] = []
                toml.write(settings)
                logger.info(f"NFC assignment reset for compartment {self.compartment}.")
            self.compartment = ""
            
        else:
            self.compartment = self.compartment + data
            
    def open_compartment(self, compartment, reason):
        if compartment not in hardware.compartments:
            dlg = ft.AlertDialog(
                    modal=False,
                    title=ft.Text("Ungültiges Fach"),
                    content=ft.Text(f"Fach {compartment} existiert nicht.",  style=ft.TextStyle(size=20)),
                    on_dismiss=None)
            self.page.open(dlg)
            time.sleep(3)
            self.page.close(dlg)
            return False
        dlg = ft.AlertDialog(
                    modal=False,
                    title=ft.Text("Fach öffnen"),
                    content=ft.Text(f"Fach {compartment} wird geöffnet.",  style=ft.TextStyle(size=20)),
                    on_dismiss=None)
        self.page.open(dlg)
        hardware.compartments[compartment].set_LEDs("white")
        success = hardware.compartments[compartment].open()
        time.sleep(3)
        if success:
           announcement = f"Bitte Fach {compartment} wieder schliessen."
           if reason == "borrow":
               question = "Hast du den Inhalt entnommen?"
               destination_yes = self.welcome
               destination_no = self.borrowing
           elif reason == "return":
               question = "Hast du den Inhalt zurückgelegt?"
               destination_yes = self.welcome
               destination_no = self.returning
           elif reason == "service":
               question = "Möchtest du ein weiteres Fach öffnen?"
               destination_yes = self.service
               destination_no = self.welcome
        else:
           announcement = f"Fach {compartment} hat sich nicht geöffnet."
           question = "Erneut versuchen?"
           if reason == "borrow":
               destination_yes = self.borrowing
               destination_no = self.welcome
           elif reason == "return":
               destination_yes = self.returning
               destination_no = self.welcome
           elif reason == "service":
               destination_yes = self.service
               destination_no = self.welcome
        dlg_modal = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Fach wurde geöffnet"),
                    content=ft.Text(f"{announcement} {question}",  style=ft.TextStyle(size=20)),
                    actions=[ft.TextButton("Nein", on_click=lambda e: self.close_modal(dlg_modal, destination_no), style=ft.ButtonStyle(text_style=ft.TextStyle(size=20, weight=ft.FontWeight.BOLD))), 
                             ft.TextButton("Ja", on_click=lambda e: self.close_modal(dlg_modal, destination_yes), style=ft.ButtonStyle(text_style=ft.TextStyle(size=20, weight=ft.FontWeight.BOLD)))],
                    on_dismiss=None)
        self.page.open(dlg_modal)
        # close dialog if no user reaction
        close_time = time.time() + 20
        while time.time() < close_time and dlg_modal.open == True:
            time.sleep(0.1)
        if dlg_modal.open == True:
            self.close_modal(dlg_modal, self.welcome)
        hardware.compartments[compartment].set_LEDs("off")
        return True
        
    def close_modal(self, dialog, destination):
        self.page.close(dialog)
        self.page_reconfigure(destination)
        
    def open_all_clicked(self, e):
        logger.info(f"All compartments opened from service mode.")
        helpers.open_all(hardware.compartments)
        
    def mounting_clicked(self, e):
        logger.info(f"Mounting compartments opened from service mode.")
        helpers.open_mounting(hardware.compartments)
        
    def reconfigure_appbar():
        pass # TODO
        
# check if given code is in dict of valid codes. return compartment and status message
def check_code(code):
    if len(code) == 4:  # normal codes have 4 digits
        status_code, valid_codes = flink.get_codes()  # get codes from Flink
        if status_code != 200:
            logger.error(f"Error response from Flink when getting codes: {status_code}")
            return None, "error"
        if valid_codes is not None:
            for comp, comp_codes in valid_codes.items():
                if code in comp_codes:
                    return comp, "valid"
        return None, "invalid"
    else:
        return None, "invalid"
        
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

if __name__ == '__main__':
    ft.app(target=UI())