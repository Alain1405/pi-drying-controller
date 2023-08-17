import sys, signal

# import schedule


from datetime import datetime, timedelta, time
import logging
from schedule_control import ScheduleControl

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


logger = logging.getLogger()


if __name__ == "__main__":

    # Every relay status defaults to 0
    # which means that at every new schedule
    # we only need to specify which relays are on
    schedule = {
        "start_time": None,
        "actuators": [0, 1, 2, 3, 4, 5, 6, 7, 8],
        "schedule": [
            {
                "duration": 5,  # minutes,
                "actions": [
                    {"id": 1, "status": 1},
                    {"id": 2, "status": 1},
                ],
            },
            {
                "duration": 5,  # minutes,
                "actions": [
                    {"id": 0, "status": 1},
                    {"id": 4, "status": 1},
                    {"id": 5, "status": 1},
                    {"id": 6, "status": 1},
                ],
            },
            {
                "duration": 5,  # minutes,
                "actions": [
                    {"id": 2, "status": 1},
                    {"id": 3, "status": 1},
                    {"id": 7, "status": 1},
                    {"id": 8, "status": 1},
                ],
            },
        ],
    }
    scheduler = ScheduleControl(schedule, start_delay=5, monitor=True)

    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        scheduler.clear()

    def signal_handler(signal, frame):
        logging.info("\nExiting gracefully")
        scheduler.stop()
        # Safely turn all relays off
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)


    try:
        logging.info("Starting scheduler")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
