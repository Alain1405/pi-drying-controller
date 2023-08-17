from apscheduler.schedulers.background import BlockingScheduler
from datetime import datetime, timedelta
from actuators_control import ActuatorsControl
import logging
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


class ScheduleControl:
    scheduler = None
    actuators_control = None

    def __init__(self, schedule, scheduler_class=BlockingScheduler, start_delay=5, monitor=True) -> None:
        self.actuators_control = ActuatorsControl(schedule)
        # Init scheduler
        self.scheduler = scheduler_class()

        # Init schedule
        task_start_time = (
            schedule["start_time"] if schedule["start_time"] else datetime.now()
        )
        task_start_time = task_start_time + timedelta(seconds=start_delay)

        # Print the list of scheduled jobs
        if monitor:
            self.scheduler.add_job(self.scheduler.print_jobs, "interval", seconds=5, id=f"monitor")

        task_delay = 0  # minutes
        for idx, interval in enumerate(schedule["schedule"]):
            task_start_time += timedelta(seconds=task_delay)

            self.scheduler.add_job(
                self.actuators_control.execute_actions,
                "date",
                run_date=task_start_time,
                id=f"job-action-{idx}",
                args=[interval["actions"]],
            )

            task_delay += interval["duration"]

        task_start_time += timedelta(seconds=task_delay)
        self.scheduler.add_job(self.stop, "date", run_date=task_start_time, id=f"shutdown")

    def stop(self):
        logging.info(f"Shutting down all actuators and schedules")
        self.scheduler.shutdown(wait=False)
        self.actuators_control.reset()

    def clear(self):
        logging.info(f"Clearing all jobs")
        self.scheduler.remove_all_jobs()

    def start(self):
        logging.info(f"Starting scheduler")
        self.scheduler.start()
