from datetime import datetime, timedelta
from actuators_control import ActuatorsControl

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.jobstores.memory import MemoryJobStore

from settings import DB_PATH

import logging

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)


class ScheduleControl:
    scheduler = None
    actuators_control = None

    def __init__(
        self, schedule, scheduler_class=BackgroundScheduler, start_delay=5, monitor=True, monitor_interval=10
    ) -> None:
        jobstore = SQLAlchemyJobStore(url=str(DB_PATH))
        self.actuators_control = ActuatorsControl(schedule)
        # Init scheduler
        self.scheduler = scheduler_class()
        self.scheduler.add_jobstore(jobstore, "default")
        self.scheduler.add_jobstore(MemoryJobStore(), "memory")

        # Init schedule
        task_start_time = (
            schedule["start_time"] if schedule["start_time"] else datetime.now()
        )
        task_start_time = task_start_time + timedelta(seconds=start_delay)

        # We need to start the scheduler in order to retrieve jobs from the jobstore
        self.scheduler.start()
        # We might be in a restart.
        # If there are other jobs, let's no schedule new ones
        # TODO: Allow to reset previous schedules on startup
        existing_jobs = self.scheduler.get_jobs(jobstore="default")
        logging.info(f"Found existing jobs {existing_jobs}")
        if not len(existing_jobs):
            logging.info("Scheduling new jobs")
            task_delay = 0  # minutes
            for idx, interval in enumerate(schedule["schedule"]):
                task_start_time += timedelta(seconds=task_delay)

                self.scheduler.add_job(
                    self.actuators_control.execute_actions,
                    jobstore="default",
                    trigger="date",
                    run_date=task_start_time,
                    id=f"job-action-{idx}",
                    args=[interval["actions"]],
                )

                task_delay += interval["duration"]

            task_start_time += timedelta(seconds=task_delay)
            self.scheduler.add_job(
                self.actuators_control.reset,
                jobstore="default",
                trigger="date",
                run_date=task_start_time,
                id=f"shutdown"
            )
        else:
            if not self.scheduler.get_job("shutdown"):
                raise Exception("Existing scheduler found, but no shutdown job was found")
            logging.info("Restarting existing schedule")

        # Print the list of scheduled jobs
        # We use the memory store here as print_jobs cannot be
        # serialized and doesn't work with DB stores.
        if monitor:
            self.scheduler.add_job(
                self.scheduler.print_jobs,
                "interval",
                seconds=monitor_interval,
                id="scheduler-monitor",
                jobstore="memory",
                kwargs={"jobstore": "default"},
            )

    def stop(self):
        logging.info(f"Shutting down all actuators and schedules")
        self.scheduler.shutdown(wait=False)
        self.actuators_control.reset()

    def clear(self):
        logging.info(f"Clearing all jobs")
        self.scheduler.remove_all_jobs()

    def start(self):
        if not self.scheduler.running:
            logging.info(f"Starting scheduler")
            self.scheduler.start()
        else:
            logging.info(f"Scheduler already running")
