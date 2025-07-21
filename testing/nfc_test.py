from nfc import NFC
from tomlkit.toml_file import TOMLFile

toml = TOMLFile("settings.toml")
settings = toml.read()

try: 
    nfc = NFC(settings["NFC"], "/dev/ttyAMA3")

except Exception as e:
    nfc = None
    print(f"Error setting up NFC: {e}")
    
while True:
    # check if NFC tag is present, timeout=0.5 s                       
    if nfc is not None:
        try:
            uid = nfc.check()
            
            if uid is not None:
                print(f"NFC tag with UID {uid} was scanned.")                
                for comp, comp_tags in settings["NFC-tags"].items():
                    if uid in comp_tags:
                        if comp == "service":
                            print("Service")
                        else:
                            print(comp)
        except Exception as e:
            print(f"Error checking NFC tag: {e}")