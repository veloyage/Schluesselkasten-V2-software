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

