import sys, signal

import logging
from schedule_control import ScheduleControl
from tb_device_client import RPIDevice
from settings import PUBLISHING_INTERVAL
import time
import os

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)


# from settings import DB_PATH
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


if __name__ == "__main__":
    # Every relay status defaults to 0
    # which means that at every new schedule
    # we only need to specify which relays are on
    schedule = {
        "start_time": None,
        "actuators": [
            {"id": 0, "label": "Light"},
            {"id": 1, "label": "Fan 1"},
            {"id": 2, "label": "Heat"},
            {"id": 3, "label": "Fan 3"},
            {"id": 4, "label": "Fan 4"},
            {"id": 5, "label": "Fan 5"},
            {"id": 6, "label": "Fan 6"},
            {"id": 7, "label": "Fan 7"},
            {"id": 8, "label": "Fan 8"},
        ],
        "schedule": [
            {
                "duration": 30,  # minutes,
                "actions": [
                    {"id": 1, "status": 1},
                    {"id": 2, "status": 1},
                ],
            },
            {
                "duration": 30,  # minutes,
                "actions": [
                    {"id": 0, "status": 1},
                    {"id": 4, "status": 1},
                    {"id": 5, "status": 1},
                    {"id": 6, "status": 1},
                ],
            },
            {
                "duration": 30,  # minutes,
                "actions": [
                    {"id": 2, "status": 1},
                    {"id": 3, "status": 1},
                    {"id": 7, "status": 1},
                    {"id": 8, "status": 1},
                ],
            },
        ],
    }
    scheduler = ScheduleControl(schedule, start_delay=5)

    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        scheduler.clear()

    def signal_handler(signal, frame):
        logging.info("\nExiting gracefully")
        scheduler.stop()
        # Safely turn all relays off
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        pi = RPIDevice(
            os.getenv("THINGSBOARD_PI_ACCESS_TOKEN"),
        )
        logging.info("Starting scheduler")
        scheduler.start()
        while True:
            pi.publish()
            time.sleep(PUBLISHING_INTERVAL)

    except (KeyboardInterrupt, SystemExit):
        pass
