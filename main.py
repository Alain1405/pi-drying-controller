import sys, signal

import logging
from schedule_control import ScheduleControl
from tb_device_client import RPIDevice, TempHumDevice
from actuators_control import CameraActuator, DummyActuator

from settings import PUBLISHING_INTERVAL, PHOTO_INTERVAL
import time
import os

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


if __name__ == "__main__":
    camera = CameraActuator("camera")
    relay_1 = DummyActuator("relay_1")
    relay_2 = DummyActuator("relay_2")
    fan = DummyActuator("fan")
    heater = DummyActuator("heater")

    # Every relay status defaults to 0
    # which means that at every new schedule
    # we only need to specify which relays are on
    schedule = {
        "start_time": None,
        "schedule": [
            {
                "duration": 30,  # minutes,
                "actions": [
                    {"actuator": relay_1, "status": 1},
                    {"actuator": relay_2, "status": 1},
                ],
            },
            {
                "duration": 30,  # minutes,
                "actions": [
                    {"actuator": fan, "status": 1},
                    {"actuator": heater, "status": 1},
                ],
            },
            {
                "duration": 30,  # minutes,
                "actions": [
                    {"actuator": relay_1, "status": 1},
                    {"actuator": heater, "status": 1},
                ],
            },
        ],
        "intervals": [
            {
                # Take a picture evet 30 min
                "interval": 30,
                "actuator": camera,
                "status": 1,
            },
            {
                # Take a picture evet 30 min
                "interval": 5,
                "actuator": relay_1,
                "status": 1,
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
        th = TempHumDevice(
            os.getenv("THINGSBOARD_TH_ACCESS_TOKEN"),
        )
        logging.info("Starting scheduler")
        scheduler.start()
        while True:
            logger.info("Publishing")
            pi.publish()
            th.publish()
            time.sleep(PUBLISHING_INTERVAL)

    except (KeyboardInterrupt, SystemExit):
        pass
