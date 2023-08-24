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
    actuators: ActuatorsControl = None

    def __init__(
        self,
        schedule,
        scheduler_class=BackgroundScheduler,
        start_delay=5,
        monitor=True,
        monitor_interval=10,
    ) -> None:
        self.actuators = ActuatorsControl()
        jobstore = SQLAlchemyJobStore(url=str(DB_PATH))
        # self.actuators_control = ActuatorsControl(schedule)
        # Init scheduler
        self.scheduler = scheduler_class()
        self.scheduler.add_jobstore(jobstore, "default")
        self.scheduler.add_jobstore(MemoryJobStore(), "memory")

        # We need to start the scheduler in order to retrieve jobs from the jobstore
        self.scheduler.start()
        self._process_schedule(schedule, start_delay)
        self._process_intervals(schedule)
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
        # self.scheduler.shutdown()

    def _process_intervals(self, schedule):
        # These are tasks that are triggered preiodically
        # We store them in memory as on restart we can just recreate them

        # Make sure actuators are passed to the controller
        self.actuators.from_actions(schedule["intervals"])

        for idx, action in enumerate(schedule["intervals"]):

            actuator = action["actuator"]
            actuator_id = id(actuator)
            value = action["status"]
            interval = action["interval"]

            self.scheduler.add_job(
                actuator.trigger,
                jobstore="default",
                trigger="interval",
                minutes=interval,
                id=f"job-{idx}-{actuator_id}",
                args=[value],
            )

    def _process_schedule(self, schedule, start_delay):
        # Init schedule
        task_start_time = (
            schedule["start_time"] if schedule["start_time"] else datetime.now()
        )
        task_start_time = task_start_time + timedelta(seconds=start_delay)
        # We might be in a restart.
        # If there are other jobs, let's no schedule new ones
        # TODO: Allow to reset previous schedules on startup
        existing_jobs = self.scheduler.get_jobs(jobstore="default")

        logging.info(f"Found existing jobs {existing_jobs}")
        if not len(existing_jobs):
            logging.info("Scheduling new jobs")
            task_delay = 0  # minutes
            for idx, interval in enumerate(schedule["schedule"]):
                task_start_time += timedelta(minutes=task_delay)
                actions = []
                # Make sure actuators are passed to the controller
                self.actuators.from_actions(interval["actions"])
                for action in interval["actions"]:
                    actuator = action["actuator"]
                    actuator_id = id(actuator)
                    actions.append(
                        {"actuator_id": actuator_id, "status": action["status"]}
                    )

                self.scheduler.add_job(
                    self.actuators.trigger_actuators,
                    jobstore="default",
                    trigger="date",
                    run_date=task_start_time,
                    id=f"job-{idx}-{actuator_id}",
                    args=[actions],
                )

                task_delay += interval["duration"]

            task_start_time += timedelta(minutes=task_delay)
            self.scheduler.add_job(
                self.actuators.reset_actuators,
                jobstore="default",
                trigger="date",
                run_date=task_start_time,
                id=f"shutdown",
            )
        else:
            if not self.scheduler.get_job("shutdown"):
                raise Exception(
                    "Existing scheduler found, but no shutdown job was found"
                )
            logging.info("Keeping existing schedule")

    def stop(self):
        logging.info(f"Shutting down all actuators and schedules")
        self.scheduler.shutdown(wait=False)
        self.actuators.reset_actuators()

    def clear(self):
        logging.info(f"Clearing all jobs")
        self.scheduler.remove_all_jobs()

    def start(self):
        if not self.scheduler.running:
            logging.info(f"Starting scheduler")
            self.scheduler.start()
        else:
            logging.info(f"Scheduler already running")
