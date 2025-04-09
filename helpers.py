import flink
import logging


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