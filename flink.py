import time
import logging
import requests

flink_timeout = 5
logger = logging.getLogger(__name__)

def format_time():
    t = time.localtime()
    return f"{t.tm_year}-{t.tm_mon:02}-{t.tm_mday:02}_{t.tm_hour:02}-{t.tm_min:02}-{t.tm_sec:02}"
 

class Flink():
    def __init__(self, ID, flink_URL, flink_API_key):
        self.ID = ID
        self.flink_URL = flink_URL
        self.flink_API_key = flink_API_key
        

    # send status to Flink
    def put_status(self, uptime, SN, version, comps, large_comps):
        try:
            response = requests.put(
                f"{self.flink_URL}/{self.ID}/status",
                headers={"Authorization": self.flink_API_key},
                json={
                    "time": format_time(),
                    "uptime": f"{uptime}",
                    "serial": f"{SN}",
                    "version": f"{version}",
                    "compartments": f"{comps}",
                    "large_compartments": f"{large_comps}",
                },
                timeout=flink_timeout,
            )
            return response.status_code
        except Exception as e:
            logger.error(f"Error putting status: {e}")
            return e


    # get codes from Flink
    def get_codes(self):
        try:
            response = requests.get(
                f"{self.flink_URL}/{self.ID}/codes",
                headers={"Authorization": self.flink_API_key},
                timeout=flink_timeout,
            )
            return response.status_code, response.json()
        except Exception as e:
            logger.error(f"Error getting codes: {e}")
            return e, None


    def post_code_log(self, code, compartments, compartment_index):
        if (compartment_index is not None) and (compartment_index in compartments):
            content = compartments[compartment_index].content_status
            door = compartments[compartment_index].door_status
        else:
            content = None
            door = None
        try:
            response = requests.post(
                f"{self.flink_URL}/{self.ID}/code_log",
                headers={"Authorization": self.flink_API_key},
                json={
                    "time": format_time(),
                    "code_entered": f"{code}",
                    "compartment": f"{compartment_index}",
                    "content": content,
                    "door": door,
                },
                timeout=flink_timeout,
            )
            return response.status_code
        except Exception as e:
            logger.error(f"Error posting code log: {e}")
            return e


class FlinkLogHandler(logging.Handler):
    def __init__(self, level, ID, flink_URL, flink_API_key):
        super().__init__(level)
        self.ID = ID
        self.flink_URL = flink_URL
        self.flink_API_key = flink_API_key
        
    def emit(self, record):
        try:
            response = requests.post(
                f"{self.flink_URL}/{self.ID}/error_log",
                headers={"Authorization": self.flink_API_key},
                json={
                    "time": format_time(),
                    "uptime": f"{record.created}",
                    "level": f"{record.levelname}",
                    "message": f"{record.msg}",
                },
                timeout=flink_timeout,
            )
        except Exception:  # ignore, otherwise we will get another error while logging
            pass
