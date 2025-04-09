# NFC communication functions
# check(): wait for a tag, read the UID and execute authentication, return UID - used to open compartments
# personalize(): wait for a tag, read UID, change master key if necessary and return UID - used to program tags to open compartments
# format(): wait for a tag, change master key back to default if necessary and return UID - used for the unlikely case of tag decommissioning

import logging

from desfire import DESFire, DESFireKey, diversify_key, get_list, to_hex_string, PN532UARTDevice
from desfire.enums import DESFireCommunicationMode, DESFireFileType, DESFireKeySettings, DESFireKeyType
from desfire.schemas import FilePermissions, FileSettings, KeySettings



logging.getLogger("desfire").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

class NFC():
    def __init__(self, settings, port):
        self.masterkey = get_list(bytearray(settings["masterkey"], 'utf-8'))
        self.app_id = get_list(bytearray(settings["app_id"], 'utf-8'))
        self.sys_id = settings["sys_id"]
        self.attempts = 20
        
        # Create physical self.device which can be used to detect a card
        self.device = PN532UARTDevice(port, baudrate=115200, timeout=0.1)   

    def personalize(self):
        MIFARE_PICC_MASTER_KEY = self.masterkey
        MIFARE_APP_ID = self.app_id  # ZEK = 5a454b = 90, 69, 75
        MIFARE_ACL_READ_BASE_KEY_ID = 0x0
        MIFARE_ACL_WRITE_BASE_KEY_ID = 0x0
        MIFARE_SYS_ID = self.sys_id  # 3 bytes, can essentially be anything
        MIFARE_ENCRYPTED_FILE_ID = 0x1

        # Wait for a card
        uid = None
        i = 0

        while not uid and i < self.attempts :
            uid = self.device.wait_for_card(timeout=1)
            i += 1

        if not uid:
            logger.warning("No card detected!")
            return None

        logger.info("Card detected.")

        # Create DESFire object, which allows further communication with the card
        desfire = DESFire(self.device)

        key_settings = desfire.get_key_setting()

        aes_key_settings = KeySettings(
            settings=[
                DESFireKeySettings.KS_ALLOW_CHANGE_MK,
                DESFireKeySettings.KS_LISTING_WITHOUT_MK,
                DESFireKeySettings.KS_CONFIGURATION_CHANGEABLE,
            ],
            key_type=DESFireKeyType.DF_KEY_AES,
            )

        # check if the card has the default key or a new one
        if key_settings.key_type == DESFireKeyType.DF_KEY_AES: # already has (our) AES key
            PICC_key = DESFireKey(key_settings, MIFARE_PICC_MASTER_KEY)
        else:   # if not, it's probably a fresh card with the default DES key
            PICC_key = DESFireKey(key_settings, "00" * 8)

        # authenticate with the key
        desfire.authenticate(0x0, PICC_key)

        # change PICC key if necessary
        if key_settings.key_type != DESFireKeyType.DF_KEY_AES:
            # Change  master key
            aes_master_key = DESFireKey(aes_key_settings, MIFARE_PICC_MASTER_KEY)
            desfire.change_key(0x00, PICC_key, aes_master_key, 0x1)

            # Re-Authenticate with new AES key
            desfire.authenticate(0x0, aes_master_key)
            PICC_key = aes_master_key

        # generate app key
        diversification_data = [0x01] + uid + get_list(MIFARE_APP_ID) + get_list(MIFARE_SYS_ID)
        div_key = diversify_key(MIFARE_PICC_MASTER_KEY, diversification_data, pad_to_32=False)
        app_key = DESFireKey(aes_key_settings, div_key)

        # check if application already present
        applications = desfire.get_application_ids()
        if MIFARE_APP_ID not in applications:
            # Set default app key           
            desfire.change_default_key(app_key, 0x0)

            # Create application
            app_settings = KeySettings(
                settings=[
                    DESFireKeySettings.KS_ALLOW_CHANGE_MK,
                    DESFireKeySettings.KS_CONFIGURATION_CHANGEABLE,
                ],
                key_type=DESFireKeyType.DF_KEY_AES,
            )

            desfire.create_application(MIFARE_APP_ID, app_settings, 4)

        # Verify application creation
        applications = desfire.get_application_ids()
        assert len(applications) == 1
        assert applications[0] == get_list(MIFARE_APP_ID)

        # Select application
        desfire.select_application(MIFARE_APP_ID)

        # Authenticate with AES key, as this has been set as the default key
        desfire.authenticate(0x0, app_key)

        # check if file exists
        files = desfire.get_file_ids()
        if MIFARE_ENCRYPTED_FILE_ID not in files:
            file_settings = FileSettings(
                file_size=16,
                encryption=DESFireCommunicationMode.ENCRYPTED,
                permissions=FilePermissions(
                    read_key=MIFARE_ACL_READ_BASE_KEY_ID,
                    write_key=MIFARE_ACL_WRITE_BASE_KEY_ID,
                ),
                file_type=DESFireFileType.MDFT_STANDARD_DATA_FILE,
            )
            desfire.create_standard_file(MIFARE_ENCRYPTED_FILE_ID, file_settings)
            
        file_data = desfire.get_file_settings(MIFARE_ENCRYPTED_FILE_ID)

        data = MIFARE_PICC_MASTER_KEY
        desfire.write_file_data(MIFARE_ENCRYPTED_FILE_ID, 0x0, file_data.encryption, get_list(data))

        rdata = desfire.read_file_data(MIFARE_ENCRYPTED_FILE_ID, file_data)
        assert rdata == data

        logger.info("Personalization finished.")
        return to_hex_string(uid)


    def check(self):

        MIFARE_PICC_MASTER_KEY = self.masterkey
        MIFARE_APP_ID = self.app_id  # ZEK = 5a454b = 90, 69, 75
        MIFARE_ACL_READ_BASE_KEY_ID = 0x0
        MIFARE_ACL_WRITE_BASE_KEY_ID = 0x0
        MIFARE_SYS_ID = self.sys_id  # 3 bytes, can essentially be anything
        MIFARE_ENCRYPTED_FILE_ID = 0x1

        aes_key_settings = KeySettings(
            settings=[
                DESFireKeySettings.KS_ALLOW_CHANGE_MK,
                DESFireKeySettings.KS_LISTING_WITHOUT_MK,
                DESFireKeySettings.KS_CONFIGURATION_CHANGEABLE,
            ],
            key_type=DESFireKeyType.DF_KEY_AES,
            )

        # Wait for a card
        uid = None
        i = 0

        #while not uid and i < self.attempts:
        uid = self.device.wait_for_card(timeout=1)
            #i += 1

        if not uid:
            #logger.error("No card detected!")
            return None

        try:
            # Create DESFire object, which allows further communication with the card
            desfire = DESFire(self.device)

            #key_settings = desfire.get_key_setting()
            PICC_key = DESFireKey(aes_key_settings, MIFARE_PICC_MASTER_KEY)

            # authenticate with the key
            desfire.authenticate(0x0, PICC_key)

            # Select application
            desfire.select_application(MIFARE_APP_ID)

            # Authenticate with app key
            diversification_data = [0x01] + uid + get_list(MIFARE_APP_ID) + get_list(MIFARE_SYS_ID)
            div_key = diversify_key(MIFARE_PICC_MASTER_KEY, diversification_data, pad_to_32=False)
            app_key = DESFireKey(aes_key_settings, div_key)
            desfire.authenticate(0x0, app_key)

            file_data = desfire.get_file_settings(MIFARE_ENCRYPTED_FILE_ID)

            rdata = desfire.read_file_data(MIFARE_ENCRYPTED_FILE_ID, file_data)
            assert rdata == MIFARE_PICC_MASTER_KEY
            logger.info(f"Card valid.")
            return ("0x" + to_hex_string(uid).replace(' ', ''))

        except Exception as e:
            logger.info(f"Card invalid: {e}")
            return None

    def format(self):

        MIFARE_PICC_MASTER_KEY = self.masterkey
        
        # Wait for a card
        uid = None
        i = 0

        # known keys, current is last
        keys = [
            get_list(bytearray(b'ZE_MasterKey2025').hex()),
            MIFARE_PICC_MASTER_KEY,
            ]


        while not uid and i < self.attempts:
            uid = self.device.wait_for_card(timeout=1)
            i += 1

        if not uid:
            #logger.error("No card detected!")
            return None

        #logger.info(f"Card detected: {uid}")

        # Create DESFire object, which allows further communication with the card
        desfire = DESFire(self.device)

        # check if the card has the default key or a new one
        key_settings = desfire.get_key_setting()
        if key_settings.key_type == DESFireKeyType.DF_KEY_AES: # already has (our) AES key
            logger.debug("AES key auth")
            # try possible (old) keys
            for key in keys:
                try:
                    PICC_key = DESFireKey(key_settings, key)
                    desfire.authenticate(0x0, PICC_key)
                    # if auth succeeds
                    new_PICC_key = DESFireKey(key_settings, keys[-1])
                    desfire.change_key(0x00, PICC_key, new_PICC_key, 0x1)
                    # reauth
                    desfire.authenticate(0x0, new_PICC_key)
                except:
                    pass
        else:   # if not, it's probably a fresh card with the default DES key
            logger.debug("DES key auth")
            PICC_key = DESFireKey(key_settings, "00" * 8)
            # authenticate with the key
            desfire.authenticate(0x0, PICC_key)

        # Format card. WARNING: This will delete all applications and files on the card!
        desfire.format_card()
        logger.info("Card formatted.")
        return to_hex_string(uid)
