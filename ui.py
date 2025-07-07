import flet as ft
import time
import subprocess

import logging
import platform

import hardware_V2 as hardware

logging.getLogger("flet").setLevel(logging.WARNING)
logging.getLogger("flet_web").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

__version__ = "2.0.0-beta1"

def start_GUI(settings, toml, flink, nfc, errors, background_tasks):
    ft.app(target=UI(settings, toml, flink, nfc, errors, background_tasks))

class DigitButton(ft.ElevatedButton):
    def __init__(self, button_clicked, text = None):
        super().__init__()
        self.text = text
        self.on_click = button_clicked
        self.data = text
        self.expand = 1
        self.padding = 0
        self.style=ft.ButtonStyle(text_style=ft.TextStyle(size=60, weight=ft.FontWeight.BOLD), shape=ft.RoundedRectangleBorder(radius=30))
        self.bgcolor = ft.Colors.WHITE


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
    def __init__(self, settings, toml, flink, nfc, errors, background_tasks):
        self.__page = None
        self.main_color = settings["UI_color"]
        self.settings = settings
        self.toml = toml
        self.flink = flink
        self.nfc = nfc
        self.errors = errors
        self.background_tasks = background_tasks
        
    def __call__(self, flet_page: ft.Page):
        self.page = flet_page
        self.page.title = "Schlüsselkasten V2"
        self.page.window.height = 800
        self.page.window.width = 480
        self.page.window.frameless = True
        self.page.window.full_screen = True
        self.page.bgcolor = ft.Colors.GREY_200
        self.page.theme = ft.Theme(color_scheme_seed=self.main_color)
         
        # all the different page setups
        
        self.welcome = ft.Column(
                        controls=[
                            ft.Card(ft.Container(ft.Image(src=f"logo.png", width=800, height=100, fit=ft.ImageFit.CONTAIN,), padding=10), color=ft.Colors.WHITE, margin=0),
                            ft.Card(content=ft.Container(content=ft.Text(value="Willkommen beim Schlüsselkasten von Ziemann Engineering. \nWas möchtest du tun?", color=self.main_color, text_align=ft.TextAlign.LEFT, size=35, style=ft.TextStyle(weight=ft.FontWeight.BOLD)), padding=15),color=ft.Colors.WHITE, margin=0),
                            ft.ElevatedButton(on_click=lambda _: self.page_reconfigure(self.booking), icon=ft.Icons.EVENT, icon_color=ft.Colors.WHITE, text=" Buchen", color = ft.Colors.WHITE, bgcolor = self.main_color, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=30), padding=20, icon_size=45, text_style=ft.TextStyle(size=35))),
                            ft.ElevatedButton(on_click=lambda _: self.page_reconfigure(self.borrowing), icon=ft.Icons.OUTPUT,icon_color=ft.Colors.WHITE, text=" Ausleihen", color = ft.Colors.WHITE, bgcolor = self.main_color, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=30), padding=20, icon_size=45, text_style=ft.TextStyle(size=35))),
                            ft.ElevatedButton(on_click=lambda _: self.page_reconfigure(self.returning), icon=ft.Icons.EXIT_TO_APP,icon_color=ft.Colors.WHITE, text=" Zurückgeben", color = ft.Colors.WHITE, bgcolor = self.main_color, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=30), padding=20, icon_size=45, text_style=ft.TextStyle(size=35))),
                        ],
                        spacing=30
                    )
                    
        self.help = ft.Column(
                        controls=[
                            ft.Card(content=ft.Container(content=ft.Text(value="Kurzanleitung", color=self.main_color, text_align=ft.TextAlign.LEFT, size=35, style=ft.TextStyle(weight=ft.FontWeight.BOLD)), padding=10),color=ft.Colors.WHITE, margin=0),
                            ft.Card(content=ft.Container(content=ft.Text(value="An diesem Schlüsselkasten kannst du Schlüssel und andere Gegenstände ausleihen. So geht's:", color=self.main_color, text_align=ft.TextAlign.LEFT, size=19, style=ft.TextStyle(weight=ft.FontWeight.BOLD)), padding=10, margin=0, expand=True),color=ft.Colors.WHITE, margin=0),
                            ft.Card(content=ft.Row([
                                ft.Container(ft.Icon(name=ft.Icons.EVENT, color=self.main_color, size=45), padding=10),
                                ft.Container(content=ft.Text(value="Zuerst musst du über Flink buchen. Wenn du noch keinen Zugang zu Flink hast, wende dich bitte zu den Öffnungszeiten an die Rezeption.", color=self.main_color, text_align=ft.TextAlign.LEFT, size=19, style=ft.TextStyle(weight=ft.FontWeight.BOLD)), padding=10, margin=0, expand=True)
                                ], spacing=0),
                                color=ft.Colors.WHITE, margin=0),
                            ft.Card(content=ft.Row([
                                ft.Container(ft.Icon(name=ft.Icons.OUTPUT, color=self.main_color, size=45), padding=10),
                                ft.Container(content=ft.Text(value="Nach Beginn des gebuchten Zeitraums kannst du den erhaltenen Code hier eingeben. Das entsprechende Fach öffnet sich und du kannst den Inhalt entnehmen.", color=self.main_color, text_align=ft.TextAlign.LEFT, size=19, style=ft.TextStyle(weight=ft.FontWeight.BOLD)), padding=10, margin=0, expand=True)
                                ], spacing=0),
                                color=ft.Colors.WHITE, margin=0),
                            ft.Card(content=ft.Row([
                                ft.Container(ft.Icon(name=ft.Icons.EXIT_TO_APP, color=self.main_color, size=45), padding=10),
                                ft.Container(content=ft.Text(value="Bitte komme vor Ende deiner Buchung zurück und halte den Schlüsselanhänger rechts an das Lesegerät. Das Fach öffnet sich dann für die Rückgabe.", color=self.main_color, text_align=ft.TextAlign.LEFT, size=19, style=ft.TextStyle(weight=ft.FontWeight.BOLD)), padding=10, margin=0, expand=True)
                                ], spacing=0),
                                color=ft.Colors.WHITE, margin=0),
                            ft.Card(content=ft.Row([
                                ft.Container(ft.Icon(name=ft.Icons.WARNING, color=self.main_color, size=45), padding=10),
                                ft.Container(content=ft.Text(value="Wenn du ein Problem hast, wende dich bitte zu den Öffnungszeiten an die Rezeption.", color=self.main_color, text_align=ft.TextAlign.LEFT, size=19, style=ft.TextStyle(weight=ft.FontWeight.BOLD)), padding=10, margin=0, expand=True)
                                ], spacing=0),
                                color=ft.Colors.WHITE, margin=0),
                        ],
                        spacing=10
                    )
        
        self.compartment  = ""  
        self.service_mode = ft.RadioGroup(content=ft.Column([
                                ft.Radio(value="open", label="Einzelnes Fach öffnen", label_style=ft.TextStyle(color=self.main_color, weight=ft.FontWeight.BOLD, size=24), active_color=self.main_color),
                                ft.Radio(value="program", label="NFC-Tag einem Fach zuweisen", label_style=ft.TextStyle(color=self.main_color, weight=ft.FontWeight.BOLD, size=24), active_color=self.main_color),
                                ft.Radio(value="reset", label="Fach-Tag-Zuweisung zurücksetzen", label_style=ft.TextStyle(color=self.main_color, weight=ft.FontWeight.BOLD, size=24), active_color=self.main_color)]))
        self.service_mode.value = "open"                        
        self.service = ft.Column(
                        controls=[
                            ft.Card(content=ft.Container(content=ft.Text(value="Service-Menü", color=self.main_color, text_align=ft.TextAlign.LEFT, size=35, style=ft.TextStyle(weight=ft.FontWeight.BOLD)), padding=15),color=ft.Colors.WHITE, margin=0),
                            ft.Row([
                                ft.ElevatedButton(text="App schliessen",on_click=lambda _: subprocess.call("./stop.sh"), color = ft.Colors.WHITE, bgcolor = self.main_color, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=30), padding=20, text_style=ft.TextStyle(size=24, weight=ft.FontWeight.BOLD)), expand=True),
                                ft.ElevatedButton(text="App neustarten", on_click=lambda _: subprocess.call("./start.sh"), color = ft.Colors.WHITE, bgcolor = self.main_color, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=30), padding=20, text_style=ft.TextStyle(size=24, weight=ft.FontWeight.BOLD)), expand=True),
                                ]),
                            ft.Row([
                                ft.ElevatedButton(text="Alle öffnen",on_click=self.open_all_clicked, color = ft.Colors.WHITE, bgcolor = self.main_color, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=30), padding=20, text_style=ft.TextStyle(size=24, weight=ft.FontWeight.BOLD)), expand=True),
                                ft.ElevatedButton(text="Montage-Modus", on_click=self.mounting_clicked, color = ft.Colors.WHITE, bgcolor = self.main_color, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=30), padding=20, text_style=ft.TextStyle(size=24, weight=ft.FontWeight.BOLD)), expand=True),
                                ]),
                            ft.Card(ft.Container(self.service_mode, padding = 10), color=ft.Colors.WHITE, margin=0),
                            NumberPad(self.service_callback)
                        ],
                        spacing=15
                    )
        
        self.open_comps_text = ft.Text(value="", color=self.main_color, text_align=ft.TextAlign.LEFT, size=16, style=ft.TextStyle(weight=ft.FontWeight.BOLD))
        self.network_text = ft.Text(value="", color=self.main_color, text_align=ft.TextAlign.LEFT, size=16, style=ft.TextStyle(weight=ft.FontWeight.BOLD))
        self.temp_text = ft.Text(value="", color=self.main_color, text_align=ft.TextAlign.LEFT, size=16, style=ft.TextStyle(weight=ft.FontWeight.BOLD))
        self.uptime_text = ft.Text(value="", color=self.main_color, text_align=ft.TextAlign.LEFT, size=16, style=ft.TextStyle(weight=ft.FontWeight.BOLD))
        self.error_text = ft.Text(value="", color=self.main_color, text_align=ft.TextAlign.LEFT, size=16, style=ft.TextStyle(weight=ft.FontWeight.BOLD))
        self.update_info()
        self.info = ft.Column([
                            ft.Card(ft.Container(ft.Text(value="Info", color=self.main_color, text_align=ft.TextAlign.LEFT, size=35, style=ft.TextStyle(weight=ft.FontWeight.BOLD)), padding=15),color=ft.Colors.WHITE, margin=0),
                            ft.Card(ft.Container(ft.Column([
                                ft.Text(value=f"ID String: {self.settings['ID']}", color=self.main_color, text_align=ft.TextAlign.LEFT, size=16, style=ft.TextStyle(weight=ft.FontWeight.BOLD)),
                                ft.Text(value=f"Serial number: {self.settings['SN']}", color=self.main_color, text_align=ft.TextAlign.LEFT, size=16, style=ft.TextStyle(weight=ft.FontWeight.BOLD)),
                                ft.Text(value=f"Software version: {__version__}", color=self.main_color, text_align=ft.TextAlign.LEFT, size=16, style=ft.TextStyle(weight=ft.FontWeight.BOLD)),
                                ft.Text(value=f"Hardware revision: {self.settings['HW_revision']}", color=self.main_color, text_align=ft.TextAlign.LEFT, size=16, style=ft.TextStyle(weight=ft.FontWeight.BOLD)),
                                ft.Text(value=f"Hardware platform: {hardware.get_cpu_model()}", color=self.main_color, text_align=ft.TextAlign.LEFT, size=16, style=ft.TextStyle(weight=ft.FontWeight.BOLD)),
                                ft.Text(value=f"Hardware serial: {hardware.get_cpu_serial()}", color=self.main_color, text_align=ft.TextAlign.LEFT, size=16, style=ft.TextStyle(weight=ft.FontWeight.BOLD)),
                                ft.Text(value=f"Python: {platform.python_version()}", color=self.main_color, text_align=ft.TextAlign.LEFT, size=16, style=ft.TextStyle(weight=ft.FontWeight.BOLD)),
                                ft.Text(value=f"OS: {platform.platform()}", color=self.main_color, text_align=ft.TextAlign.LEFT, size=16, style=ft.TextStyle(weight=ft.FontWeight.BOLD)),                                 
                                ft.Text(value=f"Small compartments: {self.settings['SMALL_COMPARTMENTS']}", color=self.main_color, text_align=ft.TextAlign.LEFT, size=16, style=ft.TextStyle(weight=ft.FontWeight.BOLD)),
                                ft.Text(value=f"Large compartments: {self.settings['LARGE_COMPARTMENTS']}", color=self.main_color, text_align=ft.TextAlign.LEFT, size=16, style=ft.TextStyle(weight=ft.FontWeight.BOLD)),
                                self.open_comps_text,
                                self.network_text,
                                self.temp_text,
                                self.uptime_text,
                                self.error_text,
                                ],scroll=ft.ScrollMode.AUTO),
                            padding=10), color=ft.Colors.WHITE, margin=0, expand=True),
                        ],
                        spacing=20, expand=True
                    )
        
        self.booking = ft.Column(
                        controls=[
                            ft.Card(content=ft.Container(content=ft.Text(value="Buchung", color=self.main_color, text_align=ft.TextAlign.LEFT, size=35, style=ft.TextStyle(weight=ft.FontWeight.BOLD)), padding=15),color=ft.Colors.WHITE, margin=0),
                            ft.Card(content=ft.Container(content=ft.Text(value="Buchen kannst du via Flink-App oder auf maw.flink.coop. Hier ist ein Link als QR-Code:", color=self.main_color, text_align=ft.TextAlign.LEFT, size=24, style=ft.TextStyle(weight=ft.FontWeight.BOLD)), padding=15, margin=0, expand=True),color=ft.Colors.WHITE, margin=0),
                            ft.Card(ft.Container(ft.Image(src=f"qrcode.png", width=450, height=430, fit=ft.ImageFit.CONTAIN,), padding=15), color=ft.Colors.WHITE, margin=0, expand=1),
                        ],
                        spacing=20
                    )
        
        self.code  = ""  
        self.code_display = ft.Text(value=self.code, size=180, color=self.main_color, width=460, max_lines=1, style=ft.TextStyle(height=0.9))
        self.borrowing = ft.Column(
                        controls=[
                        ft.Card(content=ft.Container(content=ft.Text(value="Ausleihe", color=self.main_color, text_align=ft.TextAlign.LEFT, size=35, style=ft.TextStyle(weight=ft.FontWeight.BOLD)), padding=15),color=ft.Colors.WHITE, margin=0),
                        ft.Card(ft.Container(ft.Text(value="Bitte gib deinen vierstelligen Code ein.", size=24, color=self.main_color, style=ft.TextStyle(weight=ft.FontWeight.BOLD)), padding=10), color=ft.Colors.WHITE),
                        ft.Card(ft.Container(self.code_display, padding=10), color=ft.Colors.WHITE), 
                        NumberPad(self.borrowing_callback)
                        ],
                        #spacing=20
                    )
                    
        self.tag=ft.Image(src="tag.png", width=100, height=70, fit=ft.ImageFit.CONTAIN, left=50, top=170, animate_position=ft.Animation(duration=2000, curve="ease"))
        self.returning = ft.Column(
                        controls=[
                            ft.Card(content=ft.Container(content=ft.Text(value="Rückgabe", color=self.main_color, text_align=ft.TextAlign.LEFT, size=35, style=ft.TextStyle(weight=ft.FontWeight.BOLD)), padding=15),color=ft.Colors.WHITE, margin=0),
                            ft.Card(content=ft.Row([
                                ft.Container(content=ft.Text(value="Bitte halte den Schlüsselanhänger an das Lesegerät auf der rechten Seite des Kastens.", color=self.main_color, text_align=ft.TextAlign.LEFT, size=24, style=ft.TextStyle(weight=ft.FontWeight.BOLD)), padding=10, margin=10, expand=True), 
                                ft.Icon(name=ft.Icons.ARROW_FORWARD, color=self.main_color, size=100)]),
                            color=ft.Colors.WHITE, margin=0),
                            ft.Stack([
                                ft.Card(ft.Container(ft.Image(src="nfc.png", width=430, height=390, fit=ft.ImageFit.CONTAIN,), padding=15), color=ft.Colors.WHITE, margin=0),
                                self.tag
                                ]),
                        ],
                        spacing=20
                    )
        
        self.info_bar_row = ft.Row(controls=[ft.Text(value="Status:", color=ft.Colors.WHITE, size=24)], alignment=ft.MainAxisAlignment.CENTER)
        self.info_bar = ft.Container(content=self.info_bar_row)
        self.titletext = ft.Text("ZE Schlüsselkasten", size=24, color=ft.Colors.WHITE)
        self.page.appbar = ft.AppBar(
            leading_width=48,
            leading=ft.IconButton(on_click=lambda _: self.page_reconfigure(self.welcome), icon=ft.Icons.ARROW_BACK,icon_color=ft.Colors.WHITE, icon_size=40),# padding=ft.padding.all(12)),
            title=self.titletext,
            #title=info_bar,
            center_title=True,
            actions=[ft.TextButton(on_click=lambda _: self.page_reconfigure(self.help), on_long_press=lambda _: self.page_reconfigure(self.info), icon=ft.Icons.HELP_OUTLINE,icon_color=ft.Colors.WHITE, style=ft.ButtonStyle(icon_size=40))], # padding=ft.padding.all(12)
            bgcolor=self.main_color,   
        )       
        
        self.page.add(self.welcome)        
        self.page.update()
        
        # recycle this thread to do background tasks
        self.background_tasks(self)
        
    def run_animation(self):
        #self.tag.animate_position=ft.Animation(duration=2000, curve="ease")
        self.tag.left = 50
        self.page.update()
        time.sleep(0.5)
        self.tag.left = 250
        self.page.update()
        
    # switch between welcome (initial), booking, borrowing, returning and service pages
    def page_reconfigure(self, destination):
        if len(self.page.controls) > 0:
           self.page.remove_at(0)
        self.page.add(destination)
        self.page.update()
        
        if destination == self.returning:
            self.run_animation()
        
    def borrowing_callback(self, data):
        if data == "x":
            self.code = ""
        elif data == "ok":
            comp, status = self.flink.check_code(self.code)
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
                    content=ft.Text(announcement, style=ft.TextStyle(size=24)),
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
                if self.compartment == "0000":
                    self.compartment = "service"
                dlg_modal = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("NFC-Tag programmieren"),
                    content=ft.Text(f"Bitte den NFC-Tag für Fach {self.compartment} rechts an den Leser halten, bis der Vorgang abgeschlossen ist.", style=ft.TextStyle(size=24)),
                    actions=[ft.TextButton("Abbrechen", on_click=lambda e: self.page.close(dlg_modal), style=ft.ButtonStyle(text_style=ft.TextStyle(size=24, weight=ft.FontWeight.BOLD)))],
                    on_dismiss=None)
                self.page.open(dlg_modal)
                if self.compartment in self.settings["NFC-tags"]:
                    if self.nfc is not None:
                        uid = self.nfc.personalize()
                    if uid is not None:
                        self.settings["NFC-tags"][self.compartment].append(uid)
                        dlg_modal.content=ft.Text(f"NFC-Tag wird Fach {self.compartment} zugewiesen.", style=ft.TextStyle(size=24))
                        self.toml.write(self.settings)
                        logger.info(f"NFC tag with UID {uid} assigned to compartment {self.compartment}.")
                    else:
                        dlg_modal.content=ft.Text(f"Kein NFC-Tag gefunden.", style=ft.TextStyle(size=24))
                        logger.warning(f"Tag assignment failed, no NFC tag found.")
                else:
                    dlg_modal.content=ft.Text(f"Fach {self.compartment} ist nicht gültig.", style=ft.TextStyle(size=24))
                    logger.info(f"Compartment {self.compartment} is not valid, NFC-tag not saved.")
                self.page.open(dlg_modal)
                time.sleep(2)
                self.page.close(dlg_modal)
            elif self.service_mode.value == "reset":
                # write dict, save to toml
                dlg_modal = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Fach zurückgesetzt"),
                    content=ft.Text(f"Die gespeicherten NFC-Tags für Fach {self.compartment} wurden gelöscht.", style=ft.TextStyle(size=24)),
                    on_dismiss=None)
                self.page.open(dlg_modal)
                self.settings["NFC-tags"][self.compartment] = []
                self.toml.write(self.settings)
                logger.info(f"NFC assignment reset for compartment {self.compartment}.")
                time.sleep(2)
                self.page.close(dlg_modal)
            self.compartment = ""
            
        else:
            self.compartment = self.compartment + data
            
    def open_compartment(self, compartment, reason):
        if compartment not in hardware.compartments:
            dlg = ft.AlertDialog(
                    modal=False,
                    title=ft.Text("Ungültiges Fach"),
                    content=ft.Text(f"Fach {compartment} existiert nicht.",  style=ft.TextStyle(size=24)),
                    on_dismiss=None)
            self.page.open(dlg)
            time.sleep(3)
            self.page.close(dlg)
            return False
        dlg = ft.AlertDialog(
                    modal=False,
                    title=ft.Text("Fach öffnen"),
                    content=ft.Text(f"Fach {compartment} wird geöffnet.",  style=ft.TextStyle(size=24)),
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
                    content=ft.Text(f"{announcement} {question}",  style=ft.TextStyle(size=24)),
                    actions=[ft.TextButton("Nein", on_click=lambda e: self.close_modal(dlg_modal, destination_no), style=ft.ButtonStyle(text_style=ft.TextStyle(size=24, weight=ft.FontWeight.BOLD))), 
                             ft.TextButton("Ja", on_click=lambda e: self.close_modal(dlg_modal, destination_yes), style=ft.ButtonStyle(text_style=ft.TextStyle(size=24, weight=ft.FontWeight.BOLD)))],
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
        hardware.open_all()
        
    def mounting_clicked(self, e):
        logger.info(f"Mounting compartments opened from service mode.")
        hardware.open_mounting()
        
    def reconfigure_appbar(self):
        if len(self.errors) > 0 and self.page.appbar.title == self.titletext:
            self.page.appbar.title = self.info_bar
            self.info_bar_row.controls = self.info_bar_row.controls[0:1] # clear symbols
            if "flink" in self.errors:
                self.info_bar_row.controls.append(ft.Icon(name=ft.Icons.CLOUD_OFF, color=ft.Colors.WHITE)) 
            if "ping" in self.errors:
                self.info_bar_row.controls.append(ft.Icon(name=ft.Icons.WIFI_OFF, color=ft.Colors.WHITE))
            if "power" in self.errors:
                self.info_bar_row.controls.append(ft.Icon(name=ft.Icons.POWER_OFF, color=ft.Colors.WHITE))
            if "battery" in self.errors:
                self.info_bar_row.controls.append(ft.Icon(name=ft.Icons.BATTERY_0_BAR, color=ft.Colors.WHITE))
            if [i for i in {"NFC", "compartments", "lux", "MQTT", "rpi"} if i in self.errors]:
                self.info_bar_row.controls.append(ft.Icon(name=ft.Icons.ENGINEERING, color=ft.Colors.WHITE))
        else:
            self.page.appbar.title = self.titletext
        self.page.update()
        
    def update_info(self):
        self.open_comps_text.value = f"Open compartments: {hardware.check_all()}"
        self.network_text.value = f"Network: {hardware.get_ESSID()}, Signal: {hardware.get_RSSI()}"
        self.temp_text.value = f"CPU temperature: {hardware.get_temp()} °C"
        self.uptime_text.value = f"Uptime: {hardware.uptime()}"
        self.error_text.value = f"Errors: {self.errors}"
        